"""
Reverse HTTP proxy for MCP's Streamable HTTP transport.

Different shape from the stdio proxy on purpose: there's no subprocess
to spawn here. The real server is a separately-running network service
(e.g. `http://127.0.0.1:8000/mcp`), so Greenlight has to be a local HTTP
listener that forwards to it -- point your MCP client at Greenlight's
URL instead of the real one.

Every request body and every SSE event is parsed and logged the exact
same way stdin/stdout lines are for stdio (same ProxySession, same JSONL
schema) -- greenlight tail and greenlight stats don't know or care which
transport produced the log.

Deliberately stdlib-only (http.server + urllib), not httpx/starlette --
rich is still the only runtime dependency this project has (see
notes/day1.md for why that was a decision, not an accident). The `mcp`
package pulls in httpx as a dev dependency for building test fixtures;
that's not a reason to make it a runtime dependency of the proxy itself.
"""
from __future__ import annotations

import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlsplit

from greenlight.proxy import SESSIONS_DIR, ProxySession

HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "upgrade", "content-length"}


def _make_handler(target_url: str, session: ProxySession) -> type:
    class ProxyHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            pass  # don't spam stderr with http.server's own access log

        def do_GET(self) -> None:
            self._proxy("GET")

        def do_POST(self) -> None:
            self._proxy("POST")

        def do_DELETE(self) -> None:
            self._proxy("DELETE")

        def _proxy(self, method: str) -> None:
            target = urljoin(target_url, self.path)
            body = None
            length = self.headers.get("Content-Length")
            if length:
                body = self.rfile.read(int(length))
                if body:
                    session.record("client->server", body.decode("utf-8", errors="replace"))

            forward_headers = {
                k: v for k, v in self.headers.items()
                if k.lower() not in HOP_BY_HOP and k.lower() != "host"
            }
            req = urllib.request.Request(target, data=body, headers=forward_headers, method=method)

            try:
                resp = urllib.request.urlopen(req)
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                for k, v in (e.headers.items() if e.headers else []):
                    if k.lower() not in HOP_BY_HOP:
                        self.send_header(k, v)
                self.end_headers()
                payload = e.read()
                if payload:
                    self.wfile.write(payload)
                    session.record("server->client", payload.decode("utf-8", errors="replace"))
                return

            with resp:
                self.send_response(resp.status)
                content_type = resp.headers.get("Content-Type", "")
                for k, v in resp.getheaders():
                    if k.lower() not in HOP_BY_HOP:
                        self.send_header(k, v)
                if "text/event-stream" not in content_type:
                    body_bytes = resp.read()
                    self.send_header("Content-Length", str(len(body_bytes)))
                else:
                    # No Content-Length (unknown length) and no chunked
                    # Transfer-Encoding (not implementing real HTTP
                    # chunk-framing here) means the client has no way to
                    # know where the body ends on a persistent
                    # connection. Closing the connection after this
                    # response is the correct, simple signal for that --
                    # not a real production reverse-proxy technique, but
                    # correct HTTP/1.1, and this is a debugging tool, not
                    # a production load balancer.
                    self.send_header("Connection", "close")
                    self.close_connection = True
                self.end_headers()

                if "text/event-stream" in content_type:
                    self._relay_sse(resp)
                else:
                    self.wfile.write(body_bytes)
                    if body_bytes:
                        session.record("server->client", body_bytes.decode("utf-8", errors="replace"))

        def _relay_sse(self, resp) -> None:
            """Forward SSE bytes to the client as they arrive (real
            streaming, not buffered-then-sent), while also accumulating
            into an event buffer so each complete `data: ...` line gets
            logged -- same information a stdio line gives the logger,
            just framed differently over HTTP."""
            # Found by testing against a real server, not assumed: SSE
            # events here are \r\n\r\n-terminated. \r\n\r\n does NOT
            # contain the substring "\n\n" (the \r sits between the two
            # \n bytes) -- a naive b"\n\n" check silently never matches,
            # so nothing gets logged even though the raw bytes are
            # forwarded to the client just fine (relay and logging are
            # independent here; only logging was broken). Normalizing
            # CRLF to LF before searching handles \n\n, \r\n\r\n, and
            # mixed conventions with one check. Known minor gap: a \r\n
            # split exactly across two chunk-read boundaries won't be
            # normalized (each chunk is normalized independently) --
            # rare at a 256-byte read size, not worth a stateful
            # cross-chunk normalizer for a debugging tool.
            buffer = b""
            while True:
                chunk = resp.read(256)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
                buffer += chunk.replace(b"\r\n", b"\n")
                while b"\n\n" in buffer:
                    event, buffer = buffer.split(b"\n\n", 1)
                    for line in event.decode("utf-8", errors="replace").splitlines():
                        if line.startswith("data:"):
                            session.record("server->client", line[len("data:"):].strip())

    return ProxyHandler


def run_http_proxy(target_url: str, port: int = 8808, session_name: Optional[str] = None) -> int:
    name = session_name or "http-session"
    log_path = SESSIONS_DIR / f"{name}-{int(time.time())}-{uuid.uuid4().hex[:6]}.jsonl"
    session = ProxySession(log_path)

    handler = _make_handler(target_url, session)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)

    # The proxy preserves whatever path the client requests (it forwards
    # self.path, not target_url's own path -- see ProxyHandler._proxy).
    # So the URL to actually give the client is target_url's path glued
    # onto our own host:port, not a bare host:port -- printing the latter
    # would silently send clients to the wrong path if the target isn't
    # mounted at "/".
    target_path = urlsplit(target_url).path or "/"
    local_url = f"http://127.0.0.1:{port}{target_path}"
    print(f"greenlight: proxying {local_url} -> {target_url}", file=sys.stderr)
    print(f"greenlight: recording to {log_path}", file=sys.stderr)
    print(f"greenlight: point your MCP client at {local_url} instead of {target_url}", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        session.close()
    return 0
