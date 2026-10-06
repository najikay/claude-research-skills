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


def test_forwarded_address_is_the_client_key(served):
    remote.Handler.limiter = remote.RateLimit(per_minute=60, burst=1)
    assert (
        post(
            served,
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.9"},
        )[0]
        == 200
    )
    assert (
        post(
            served,
            {"jsonrpc": "2.0", "id": 2, "method": "ping"},
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.9"},
        )[0]
        == 429
    )
    assert (
        post(
            served,
            {"jsonrpc": "2.0", "id": 3, "method": "ping"},
            headers={"X-Forwarded-For": "10.0.0.2"},
        )[0]
        == 200
    )


def test_bucket_refills():
    lim = remote.RateLimit(per_minute=60, burst=2)
    assert lim.allow("k", now=0.0) and lim.allow("k", now=0.0)
    assert not lim.allow("k", now=0.0)
    assert lim.allow("k", now=1.0)  # one token a second at 60 a minute


def test_log_line_never_carries_the_arguments():
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "verify_reference",
                "arguments": {"title": "A Secret Draft Title"},
            },
        }
    ).encode()
    line = remote._describe(body)
    assert line == "tools/call:verify_reference"
    assert "Secret" not in line
