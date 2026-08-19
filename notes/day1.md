# Greenlight — Day 1 notes

## What this is

A transparent stdio proxy for MCP servers. You point it at a real server
command instead of running that command directly (`greenlight run -- npx
-y @some/mcp-server`), and it relays every byte exactly as before while
recording every JSON-RPC message to a structured log. The point is
visibility: right now almost nobody debugging an MCP integration can see
what actually got sent, what came back, or why a call failed.

## What exists

* `src/greenlight/proxy.py` -- the core: spawns the real server, relays
  stdin/stdout on two threads, parses each line as JSON-RPC, logs it.
* `src/greenlight/cli.py` -- `greenlight run -- <command>`.
* `tests/fixture_server.py` -- a small *real* MCP server (official SDK,
  not a mock) with three tools: a boring one, a slow one, and one that
  always fails. Built specifically to exercise the three things the proxy
  needs to get right: normal relay, latency measurement, and error
  handling.
* `tests/test_proxy_e2e.py` -- drives a real MCP client session through
  the proxy against that fixture server and checks both that the protocol
  worked normally and that the log is accurate.

## The one rule this whole thing depends on

The proxy's own stdout may never carry anything except the child
process's actual bytes. Any log line or UI output written there would
corrupt the JSON-RPC stream the real client is parsing. Logging goes to a
JSONL file on disk; a status line to stderr is fine (MCP's stdio
transport never uses stderr for protocol traffic).

## A real bug, caught by testing against a real server instead of trusting the design

First version only flagged JSON-RPC transport-level errors (`"error" in
msg`) as failures. Tested it against `fixture_server.py`'s `boom()` tool,
which always raises -- and the log showed it as an ordinary, successful
`result`. Not a logging bug exactly: MCP nests tool-execution failures
*inside* a normal JSON-RPC result (`result.isError = true`), which is a
different thing from a transport-level error, and the first version
didn't know that distinction existed.

This matters more than it sounds like it should: a failed tool call is
close to the single most important thing a trace viewer needs to surface
in red, and the first version would have silently shown it as green.
Fixed by checking `result.isError` specifically and flagging it as
`tool_error` in the log, distinct from transport-level `error`. Caught
because the fixture server was built to have a tool that actually fails,
not just a tool that succeeds -- an end-to-end test that never exercises
the failure path can't catch a bug in how failures are handled.

## Design decisions worth remembering

* **stdio only for v1.** Most local MCP servers (the kind run via `npx`
  or a local Python/Node process) use stdio transport. HTTP/SSE proxying
  is a real feature, not needed to prove this works.
* **`rich` is the only runtime dependency.** The official `mcp` SDK is a
  dev dependency (used to build the test fixture), not something
  Greenlight itself needs -- it only has to understand JSON-RPC framing,
  not the MCP protocol semantics on top of it. Fewer runtime dependencies
  means less friction for anyone who wants to actually install this.
* **PyPI name is `greenlight-mcp`, not `greenlight`** -- that name's
  already taken. Import name and CLI command are still `greenlight`.
* **Windows PATH resolution.** `subprocess.Popen(["npx", ...])` fails on
  Windows with `shell=False` because `npx` is actually `npx.cmd` and
  Windows doesn't apply `PATHEXT` resolution the way a real shell does.
  Resolved via `shutil.which()` before spawning. Untested on an actual
  npx-based MCP server yet -- only tested against a Python fixture server
  so far, which sidesteps this exact issue. Worth testing against a real
  npx-launched server before calling Windows support solid.

## Open for next session

* The live `tail` UI -- this is the actual demo-GIF moment, doesn't exist
  yet. Log format is stable enough to build it against now.
* No handling yet for a server that writes non-JSON-RPC noise to stdout
  (some servers print startup banners before they start speaking
  protocol). Currently logged as `parsed: false` and still relayed, which
  is probably fine, but not yet tested against a server that actually
  does this.
* README doesn't exist yet -- writing docs before anyone but me has
  reason to run this would be getting ahead of the work.
