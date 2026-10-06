"""The HTTP transport around the checker: a real server on a free port, the network faked."""

import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "servers" / "reference_lookup"
spec = importlib.util.spec_from_file_location(
    "reference_lookup_remote", HERE / "remote.py"
)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
rl = remote.checker


@pytest.fixture
def served(monkeypatch):
    """A live server on 127.0.0.1 with OpenAlex and arXiv replaced by a fake that knows one paper."""
    paper = {
        "id": "https://openalex.org/W3",
        "title": "Deep Residual Learning for Image Recognition",
        "publication_year": 2016,
        "cited_by_count": 200000,
        "doi": "https://doi.org/10.1109/cvpr.2016.90",
        "authorships": [{"author": {"display_name": "Kaiming He"}}],
        "primary_location": {
            "landing_page_url": "https://x/W3",
            "source": {"display_name": "CVPR"},
        },
        "referenced_works": [],
    }

    def fetch(url, params=None):
        if "10.1109/cvpr.2016.90" in url.lower():
            return 200, json.dumps(paper)
        if url == rl.ARXIV:
            return 200, "<feed xmlns='http://www.w3.org/2005/Atom'></feed>"
        return 200, json.dumps({"results": []})

    monkeypatch.setattr(rl, "fetch", fetch)
    monkeypatch.setattr(rl.time, "sleep", lambda s: None)
    remote.Handler.limiter = remote.RateLimit()  # a fresh bucket per test
    httpd = remote.serve("127.0.0.1", 0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def post(base, payload, raw: bytes | None = None, headers=None):
    data = raw if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base + "/mcp",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read()
            return r.status, dict(r.headers), json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, dict(e.headers), json.loads(body) if body else None


def test_initialize_and_tools_list(served):
    status, headers, out = post(
        served,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "t", "version": "0"},
            },
        },
    )
    assert status == 200
    assert headers["MCP-Protocol-Version"] == rl.PROTOCOL_VERSION
    assert out["result"]["serverInfo"]["name"] == "reference-lookup"
    status, _, out = post(served, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in out["result"]["tools"]}
    assert names == {
        "verify_reference",
        "verify_bibtex",
        "lookup_reference",
        "search_works",
        "citation_neighbours",
    }
    assert all(t["annotations"]["readOnlyHint"] for t in out["result"]["tools"])
    assert all(t["title"] for t in out["result"]["tools"])


def test_a_notification_gets_202_and_no_body(served):
    status, _, out = post(
        served, {"jsonrpc": "2.0", "method": "notifications/initialized"}
    )
    assert status == 202
    assert out is None


def test_tool_call_verifies_a_reference(served):
    status, _, out = post(
        served,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "verify_reference",
                "arguments": {
                    "title": "Deep Residual Learning for Image Recognition",
                    "authors": ["He, K."],
                    "year": 2016,
                    "doi": "10.1109/CVPR.2016.90",
                },
            },
        },
    )
    assert status == 200
    assert out["result"]["isError"] is False
    verdict = json.loads(out["result"]["content"][0]["text"])
    assert verdict["status"] == "verified"
    assert verdict["matched_doi"] == "10.1109/cvpr.2016.90"


def test_a_batch_is_answered_in_order(served):
    status, _, out = post(
        served,
        [
            {"jsonrpc": "2.0", "id": "a", "method": "ping"},
            {"jsonrpc": "2.0", "method": "notifications/x"},
            {"jsonrpc": "2.0", "id": "b", "method": "tools/list"},
        ],
    )
    assert status == 200
    assert [o["id"] for o in out] == ["a", "b"]


def test_bad_json_and_wrong_shapes(served):
    status, _, out = post(served, None, raw=b"{not json")
    assert status == 400
    assert out["error"]["code"] == -32700
    status, _, out = post(served, {"jsonrpc": "2.0", "id": 9, "method": "no/such"})
    assert status == 200
    assert out["error"]["code"] == -32601
    status, _, out = post(served, None, raw=b"x" * (remote.MAX_BODY + 1))
    assert status == 413


def test_get_mcp_is_405_and_health_answers(served):
    with urllib.request.urlopen(served + "/health", timeout=5) as r:
        assert json.loads(r.read())["ok"] is True
    try:
        urllib.request.urlopen(served + "/mcp", timeout=5)
        raise AssertionError("GET /mcp must not succeed")
    except urllib.error.HTTPError as e:
        assert e.code == 405


def test_rate_limit_answers_429_with_retry_after(served):
    remote.Handler.limiter = remote.RateLimit(per_minute=60, burst=3)
    codes = [
        post(served, {"jsonrpc": "2.0", "id": i, "method": "ping"})[0] for i in range(5)
    ]
    assert codes == [200, 200, 200, 429, 429]
    status, headers, out = post(served, {"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert status == 429
    assert headers["Retry-After"] == "10"
    assert "too many requests" in out["error"]["message"]


def test_the_proxy_appended_address_is_the_client_key(served):
    """A client can write anything into X-Forwarded-For; only the last entry (the proxy's) and
    Fly's own header count."""
    remote.Handler.limiter = remote.RateLimit(per_minute=60, burst=1)
    h = {"X-Forwarded-For": "1.1.1.1, 10.0.0.9"}
    assert post(served, {"jsonrpc": "2.0", "id": 1, "method": "ping"}, headers=h)[0] == 200
    h = {"X-Forwarded-For": "2.2.2.2, 10.0.0.9"}  # a forged first entry does not buy a new bucket
    assert post(served, {"jsonrpc": "2.0", "id": 2, "method": "ping"}, headers=h)[0] == 429
    h = {"X-Forwarded-For": "2.2.2.2, 10.0.0.9", "Fly-Client-IP": "10.0.0.3"}
    assert post(served, {"jsonrpc": "2.0", "id": 3, "method": "ping"}, headers=h)[0] == 200


def test_a_batch_costs_one_token_per_message_and_is_capped(served):
    remote.Handler.limiter = remote.RateLimit(per_minute=60, burst=3)
    three = [{"jsonrpc": "2.0", "id": i, "method": "ping"} for i in range(3)]
    assert post(served, three)[0] == 200
    assert post(served, {"jsonrpc": "2.0", "id": 9, "method": "ping"})[0] == 429
    remote.Handler.limiter = remote.RateLimit()
    eleven = [{"jsonrpc": "2.0", "id": i, "method": "ping"} for i in range(11)]
    status, _, out = post(served, eleven)
    assert status == 400 and "at most 10" in out["error"]["message"]


def test_bodies_never_leak_into_the_next_request(served):
    """A chunked POST is refused; a POST elsewhere with a body closes the connection."""
    import http.client

    host, port = served.replace("http://", "").split(":")
    c = http.client.HTTPConnection(host, int(port), timeout=5)
    c.putrequest("POST", "/mcp")
    c.putheader("Transfer-Encoding", "chunked")
    c.putheader("Content-Type", "application/json")
    c.endheaders()
    r = c.getresponse()
    assert r.status == 411 and r.getheader("Connection") == "close"
    c.close()
    c = http.client.HTTPConnection(host, int(port), timeout=5)
    c.request("POST", "/elsewhere", body=b'{"jsonrpc":"2.0","id":1,"method":"ping"}', headers={"Content-Type": "application/json"})
    r = c.getresponse()
    assert r.status == 404 and r.getheader("Connection") == "close"
    c.close()


def test_a_full_bucket_is_forgotten():
    lim = remote.RateLimit(per_minute=60, burst=2)
    for i in range(remote.MAX_BUCKETS + 1):
        lim.allow(f"k{i}", now=0.0)
    assert len(lim._buckets) <= remote.MAX_BUCKETS  # the overflow was trimmed at once
    fresh = [f"n{j}" for j in range(remote.MAX_BUCKETS - len(lim._buckets) + 1)]
    for k in fresh:
        lim.allow(k, now=100.0)  # the next overflow: every old bucket has refilled by now, so they all go
    assert set(lim._buckets) == set(fresh)


def test_bucket_refills():
    lim = remote.RateLimit(per_minute=60, burst=2)
    assert lim.allow("k", now=0.0) and lim.allow("k", now=0.0)
    assert not lim.allow("k", now=0.0)
    assert lim.allow("k", now=1.0)  # one token a second at 60 a minute


def test_log_line_carries_only_known_names():
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "verify_reference", "arguments": {"title": "A Secret Draft Title"}}}).encode()
    assert remote._describe(body) == "tools/call:verify_reference"
    forged = json.dumps([{"jsonrpc": "2.0", "id": 1, "method": "A Secret Draft Title\n200 fake"}, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "Another Secret"}}]).encode()
    assert remote._describe(forged) == "other,tools/call:other"


def test_global_and_daily_ceilings(served):
    remote.Handler.limiter = remote.RateLimit()
    remote.Handler.everyone = remote.RateLimit(per_minute=60, burst=2)
    codes = [post(served, {"jsonrpc": "2.0", "id": i, "method": "ping"}, headers={"X-Forwarded-For": f"10.0.0.{i}"})[0] for i in range(3)]
    assert codes == [200, 200, 429]  # three different callers share one ceiling
    remote.Handler.everyone = remote.RateLimit()
    remote.Handler.daily = remote.DailyCap(1)
    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "search_works", "arguments": {"query": "x"}}}
    assert post(served, call)[0] == 200
    status, headers, out = post(served, call)
    assert status == 429 and headers["Retry-After"] == "3600" and "daily limit" in out["error"]["message"]
    assert post(served, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})[0] == 200  # listing costs nothing
    with urllib.request.urlopen(served + "/health", timeout=5) as r:
        assert json.loads(r.read())["tool_calls_today"] == 1


def test_daily_cap_resets_with_the_day():
    cap = remote.DailyCap(2)
    assert cap.take(2, day="2026-10-06") and not cap.take(1, day="2026-10-06")
    assert cap.take(1, day="2026-10-07")
