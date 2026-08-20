# Greenlight — Day 6 notes

## HTTP/SSE transport

Different shape from the stdio proxy, not just a variant of it: there's
no subprocess to spawn. The real server is a separately-running network
service, so Greenlight has to be a local reverse HTTP proxy instead --
point your client at Greenlight's URL, it forwards to the real one,
logs both directions the same way stdin/stdout lines get logged for
stdio. Same `ProxySession`, same JSONL schema, same `tail`/`stats`
downstream -- neither of those needed to change at all, which is the
payoff of having built the log format transport-agnostic from day 1.

Deliberately stdlib-only (`http.server` + `urllib`), not httpx/starlette,
to keep `rich` as the only runtime dependency -- see `notes/day1.md` for
why that was a decision, not an accident. The `mcp` SDK's own streamable
HTTP implementation uses `httpx` under the hood, but that's a dev
dependency for building test fixtures, not a reason to add it to
Greenlight's own runtime.

## Three real bugs, found by actually testing it, in order

1. **Wrong transport string.** Guessed `"streamableHttp"` from an
   unrelated server's `--help` output earlier in the project; the actual
   SDK's `MCPServer.run()` only accepts `"streamable-http"` (hyphenated).
   Found immediately on first run -- a `ValueError` naming the actual
   valid options, not a silent failure.

2. **SSE events silently never logged, while the actual protocol worked
   fine.** The client-through-proxy session completed successfully --
   `initialize`, `list_tools`, all three tool calls, correct results,
   correct error handling -- but the session log had zero
   `server->client` entries. Not a proxy-transparency bug (the bytes
   reached the client correctly); a *logging* bug, and one that would
   have been invisible without checking the log contents specifically,
   since the client-facing behavior looked completely correct.

   Root cause: this server frames SSE events with `\r\n\r\n`, and
   `\r\n\r\n` does not contain the substring `\n\n` -- the `\r` sits
   between the two `\n` bytes. The event-boundary check
   (`b"\n\n" in buffer`) silently never matched, so no event was ever
   considered "complete" and nothing got parsed or logged. Confirmed the
   exact wire format with a raw `urllib` request bypassing the MCP SDK
   entirely, rather than guessing at the fix. Fixed by normalizing CRLF
   to LF before searching for the boundary, so both conventions work
   with one check.

3. **The test's own before/after log-file diffing was wrong**, not the
   proxy. `test_http_proxy.py` first computed "which session log is new"
   the same way the stdio tests do -- snapshot directory contents,
   run the client session, diff. But the HTTP proxy is a standing
   process, not spawned per-connection: its log file gets created the
   instant the proxy starts, before any client traffic, so a snapshot
   taken later (right before the client connects) already includes it,
   and the diff always came up empty. Fixed by moving the snapshot to
   before the proxy process itself starts. A stdio-shaped assumption
   (one process per session) carried over into a fundamentally
   different architecture (one long-running process, many sessions)
   without being re-examined -- worth remembering as a category of bug,
   not just this specific instance of it.

## Verified, not assumed

Full loop tested against a real HTTP fixture server (same tool
definitions as the stdio fixture, run over `streamable-http` instead --
one set of tools, not two copies to drift apart): initialize, list
tools, three tool calls including the deliberate failure, latency
tracking, and confirmed `greenlight tail`/`greenlight stats` work
unmodified against the resulting log. Self-contained test -- spawns both
the fixture server and the proxy itself, no manual multi-terminal setup
required to reproduce.

## Discoverability, revisited with real data instead of guesses

Checked what topics actually co-occur on popular MCP repositories
(`gh api search/repositories?q=topic:model-context-protocol`) instead of
guessing at tags. Added `mcp-inspector` (an established topic --30 real
repos, including a 2,150-star inspector tool in the same space),
`python`, and `llm`, on top of the topics set on day 5.

Noticed `Epistates/awesome-mcp-devtools` in that search -- a curated
list repo, exactly the kind of PR target flagged earlier as
high-leverage distribution. Worth following up on, not done yet.

## Open

* Version is still 0.1.0 on PyPI; `stats` and `--http` only exist in the
  GitHub source so far. Needs a version bump + republish (my token,
  run from the user's terminal, same as the first publish) whenever
  that's worth doing.
* No tests yet for what happens when the target HTTP server is
  unreachable, or returns a genuinely malformed (non-JSON) body on the
  non-SSE path -- only the happy path and the one error path (tool
  failure) are covered.
