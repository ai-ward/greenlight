# Greenlight — Day 3 notes

## What this closes

The biggest open item from day 2: `greenlight run -- npx ...` had only
ever been reasoned about on Windows, never actually run. Tested against
`@modelcontextprotocol/server-everything` -- the official MCP reference
server, picked specifically because it's a real third party, not
something hand-built to be easy to proxy.

Full loop verified: real npx resolution through `shutil.which()`, real
handshake, real tool calls (`echo`, `get-sum`), session log correctly
recorded with no unparsed/malformed lines, `greenlight tail` renders it
correctly.

## One thing checked, not assumed: where does startup noise go

`server-everything` prints `Starting default (STDIO) server...` before
it starts speaking protocol -- exactly the "some servers print a banner"
case flagged as untested in day 2 notes. Checked directly (ran the
server standalone, redirected stdout and stderr separately): the banner
goes to stderr. Nothing for the proxy to handle -- stderr is already
inherited untouched. Worth confirming rather than assuming, since a
server that put startup noise on *stdout* would have needed the
"parsed: false" fallback path to actually be exercised, and it wasn't
here.

## Also noticed, not a bug

The trace log captured a `notifications/tools/list_changed` message from
the server, unprompted, sitting between the `tools/list` request and its
response. Proxy handled it correctly (it's a notification, not tied to
any request id, logged and displayed with no issue) -- just noting that
real servers send traffic outside the simple request/response pattern,
and the fixture server never exercised that case either.

## Status

`greenlight run` + `greenlight tail` now validated against two servers:
the hand-built Python fixture (exercises success/slow/error paths
deliberately) and a real third-party npx server (exercises the realistic
deployment shape). Different failure surfaces, both clean.

## Next: PyPI

Package builds and installs correctly from source. Publishing as
`greenlight-mcp` needs a PyPI account + API token that don't exist yet on
this machine -- that's a manual step, not something to script around.
