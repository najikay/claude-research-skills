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
JSON = "application/json"
log = logging.getLogger("reference-lookup-http")


class RateLimit:
    """A token bucket per client address. Thread-safe; old buckets are dropped as they fill back up."""

    def __init__(self, per_minute: float = RATE_PER_MINUTE, burst: int = BURST) -> None:
        self.rate = per_minute / 60.0
        self.burst = float(burst)
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            tokens, last = self._buckets.get(key, (self.burst, now))
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens < 1.0:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1.0, now)
            if len(self._buckets) > 10_000:  # forget everyone who is full again
                self._buckets = {
                    k: v for k, v in self._buckets.items() if v[0] < self.burst - 0.5
                }
            return True


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

    def client_key(self) -> str:
        fwd = self.headers.get("X-Forwarded-For", "")
        return (fwd.split(",")[0].strip() if fwd else self.client_address[0]) or "?"

    def send_json(self, status: int, payload: Any) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{JSON}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("MCP-Protocol-Version", checker.PROTOCOL_VERSION)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("MCP-Protocol-Version", checker.PROTOCOL_VERSION)
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/health", "/healthz"):
            self.send_json(
                200,
                {
                    "ok": True,
                    "name": checker.INFO["name"],
                    "version": checker.INFO["version"],
                },
            )
        elif self.path == "/" or self.path == "/mcp":
            self.send_json(
                405 if self.path == "/mcp" else 200,
                {
                    "name": "Research Desk reference checker",
                    "version": checker.INFO["version"],
                    "mcp": "POST /mcp (Streamable HTTP, stateless; no GET stream)",
                    "docs": "https://github.com/najikay/claude-research-skills",
                    "privacy": "https://github.com/najikay/claude-research-skills/blob/main/PRIVACY.md",
                },
            )
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        started = time.monotonic()
        if self.path != "/mcp":
            self.send_json(404, {"error": "not found; the MCP endpoint is /mcp"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            # read what the client is still sending (bounded) so the answer does not break its pipe
            left = min(max(length, 0), 8 * MAX_BODY)
            while left > 0:
                chunk = self.rfile.read(min(left, 65536))
                if not chunk:
                    break
                left -= len(chunk)
            self.close_connection = True
            self.send_json(413, rpc_error(None, -32600, f"the body must be at most {MAX_BODY // 1024} KB"))
            return
        body = self.rfile.read(length) if length else b""
        key = self.client_key()
        if not self.limiter.allow(key):
            self.send_response(429)
            self.send_header("Retry-After", "10")
            self.send_json_tail(
                rpc_error(
                    None,
                    -32000,
                    "too many requests from this address; wait ten seconds and try again",
                )
            )
            log.info("429")
            return
        status, payload = answer(body)
        if payload is None:
            self.send_empty(status)
        else:
            self.send_json(status, payload)
        what = _describe(body)
        log.info("%s %s %.2fs", status, what, time.monotonic() - started)  # no address, no arguments

    def send_json_tail(self, payload: Any) -> None:
        """Headers already started with send_response: finish them and write the body."""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Type", f"{JSON}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _describe(body: bytes) -> str:
    """The method and tool name for the log, never the arguments."""
    try:
        msg = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return "bad-json"
    msgs = msg if isinstance(msg, list) else [msg]
    parts = []
    for m in msgs:
        if not isinstance(m, dict):
            parts.append("?")
            continue
        method = str(m.get("method", "?"))
        if method == "tools/call" and isinstance(m.get("params"), dict):
            method += ":" + str(m["params"].get("name", "?"))
        parts.append(method)
    return ",".join(parts)[:120]


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
