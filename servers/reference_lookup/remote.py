"""The reference checker over HTTP, so it can be hosted and reached from Claude.ai.

MCP's Streamable HTTP transport, stateless: every POST to /mcp carries one JSON-RPC message (or a
batch) and gets the answers back as one JSON body. No sessions, no server-to-client stream, no
state between requests; GET /mcp answers 405. Standard library only, like the checker itself.

    python3 servers/reference_lookup/remote.py --port 8080

What it keeps: nothing. The log has one line per request with the method, the tool name, the
status and the time taken; never the reference text and never the caller's address (that is held
in memory only, for the rate limit). A per-address rate limit protects the two
public services behind it (OpenAlex, arXiv) from one busy client.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server as checker

MAX_BODY = 512 * 1024  # a BibTeX file of 60 entries is far under this
RATE_PER_MINUTE = 60  # JSON-RPC messages per client address; tools/call is what costs
BURST = 20
MAX_BATCH = 10  # JSON-RPC messages per POST; each costs a token
MAX_BUCKETS = 10_000  # client addresses remembered by the rate limiter
TIMEOUT_S = 30  # a client that stops sending mid-request is dropped after this
KNOWN_METHODS = {"initialize", "ping", "tools/list", "tools/call", "notifications/initialized", "notifications/cancelled"}
JSON = "application/json"
log = logging.getLogger("reference-lookup-http")


class RateLimit:
    """A token bucket per client address. Thread-safe; old buckets are dropped as they fill back up."""

    def __init__(self, per_minute: float = RATE_PER_MINUTE, burst: int = BURST) -> None:
        self.rate = per_minute / 60.0
        self.burst = float(burst)
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, cost: int = 1, now: float | None = None) -> bool:
        """Charge ``cost`` tokens to ``key``; False when it has too few (nothing is charged then)."""
        now = time.monotonic() if now is None else now
        with self._lock:
            tokens, last = self._buckets.get(key, (self.burst, now))
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens < cost:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - cost, now)
            if len(self._buckets) > MAX_BUCKETS:
                self._forget(now)
            return True

    def _forget(self, now: float) -> None:
        """Drop every bucket that has refilled to the brim (as if that client had never been seen)."""
        self._buckets = {k: (t, last) for k, (t, last) in self._buckets.items() if t + (now - last) * self.rate < self.burst}
        if len(self._buckets) > MAX_BUCKETS:  # still too many live clients: keep the most recent half
            self._buckets = dict(sorted(self._buckets.items(), key=lambda kv: kv[1][1])[-MAX_BUCKETS // 2 :])


def rpc_error(rid: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def answer(body: bytes) -> tuple[int, list[dict] | dict | None]:
    """One request body → (HTTP status, JSON to send). Notifications get 202 and no body."""
    try:
        msg = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return 400, rpc_error(
            None, -32700, "parse error: the body must be a JSON-RPC message"
        )
    if isinstance(msg, list):
        if not msg:
            return 400, rpc_error(None, -32600, "an empty batch")
        outs = [o for o in (checker.handle(m) for m in msg) if o is not None]
        return (200, outs) if outs else (202, None)
    out = checker.handle(msg)
    return (200, out) if out is not None else (202, None)


class Handler(BaseHTTPRequestHandler):
    server_version = f"reference-lookup/{checker.INFO['version']}"
    protocol_version = "HTTP/1.1"
    limiter = RateLimit()

    def log_message(
        self, fmt: str, *args: Any
    ) -> None:  # the default writes the request line; ours is below
        pass

    timeout = TIMEOUT_S

    def client_key(self) -> str:
        """The caller's address for the rate limit. Behind Fly the socket is the proxy's, so the proxy's
        own header wins; the LAST X-Forwarded-For entry is the one the proxy appended (the first can be
        anything the client wrote)."""
        direct = self.headers.get("Fly-Client-IP", "").strip()
        if direct:
            return direct
        fwd = self.headers.get("X-Forwarded-For", "")
        last = fwd.rsplit(",", 1)[-1].strip() if fwd else ""
        return last or self.client_address[0] or "?"

    def drain(self, length: int) -> None:
        """Read what the client is still sending (bounded) so an early answer does not break its pipe,
        then close: whatever was not read must never be taken for the next request."""
        left = min(max(length, 0), 8 * MAX_BODY)
        while left > 0:
            chunk = self.rfile.read(min(left, 65536))
            if not chunk:
                break
            left -= len(chunk)
        self.close_connection = True

    def send_json(self, status: int, payload: Any) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{JSON}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("MCP-Protocol-Version", checker.PROTOCOL_VERSION)
        self.send_header("Cache-Control", "no-store")
        if self.close_connection:
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("MCP-Protocol-Version", checker.PROTOCOL_VERSION)
        self.end_headers()

    def do_GET(self) -> None:
        if self.headers.get("Content-Length") or self.headers.get("Transfer-Encoding"):
            self.close_connection = True  # a body on a GET is never read: it must not become the next request
        if self.path in ("/health", "/healthz"):
            self.send_json(200, {"ok": True, "name": checker.INFO["name"], "version": checker.INFO["version"]})
        elif self.path in ("/", "/mcp"):
            self.send_json(405 if self.path == "/mcp" else 200, {
                "name": "Research Desk reference checker",
                "version": checker.INFO["version"],
                "mcp": "POST /mcp (Streamable HTTP, stateless; no GET stream)",
                "docs": "https://github.com/najikay/claude-research-skills",
                "privacy": "https://github.com/najikay/claude-research-skills/blob/main/PRIVACY.md",
            })
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        started = time.monotonic()
        if self.headers.get("Transfer-Encoding"):  # a chunked body is not read: say so and close
            self.close_connection = True
            self.send_json(411, rpc_error(None, -32600, "send a Content-Length; chunked bodies are not accepted"))
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if self.path != "/mcp":
            self.drain(length)
            self.send_json(404, {"error": "not found; the MCP endpoint is /mcp"})
            return
        if length < 0 or length > MAX_BODY:
            self.drain(length)
            self.send_json(413, rpc_error(None, -32600, f"the body must be at most {MAX_BODY // 1024} KB"))
            return
        body = self.rfile.read(length) if length else b""
        count = _count(body)
        if count > MAX_BATCH:
            self.send_json(400, rpc_error(None, -32600, f"at most {MAX_BATCH} messages per request"))
            return
        if not self.limiter.allow(self.client_key(), cost=count):
            self.send_response(429)
            self.send_header("Retry-After", "10")
            self.send_json_tail(rpc_error(None, -32000, "too many requests from this address; wait ten seconds and try again"))
            log.info("429")
            return
        status, payload = answer(body)
        if payload is None:
            self.send_empty(status)
        else:
            self.send_json(status, payload)
        log.info("%s %s %.2fs", status, _describe(body), time.monotonic() - started)  # no address, no arguments

    def send_json_tail(self, payload: Any) -> None:
        """Headers already started with send_response: finish them and write the body."""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Type", f"{JSON}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _parse(body: bytes) -> list[Any] | None:
    try:
        msg = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return msg if isinstance(msg, list) else [msg]


def _count(body: bytes) -> int:
    msgs = _parse(body)
    return max(1, len(msgs)) if msgs is not None else 1


def _describe(body: bytes) -> str:
    """What was asked, for the log: only names the server knows, so no client text can reach the log."""
    msgs = _parse(body)
    if msgs is None:
        return "bad-json"
    tools = {t["name"] for t in checker.TOOLS}
    parts = []
    for m in msgs:
        method = m.get("method") if isinstance(m, dict) else None
        name = method if method in KNOWN_METHODS else "other"
        if name == "tools/call" and isinstance(m.get("params"), dict):
            tool = m["params"].get("name")
            name += ":" + (tool if tool in tools else "other")
        parts.append(name)
    return ",".join(parts[:MAX_BATCH])


def serve(host: str, port: int) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    return httpd


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    a = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout
    )
    httpd = serve(a.host, a.port)
    log.info(
        "reference-lookup %s listening on %s:%s",
        checker.INFO["version"],
        a.host,
        a.port,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
