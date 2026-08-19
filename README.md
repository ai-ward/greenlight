```
  .-----.
  |  🔴  |
  |  🟡  |
  |  🟢  |
  '-----'
   greenlight
```

# greenlight

See what your MCP server is actually doing.

A transparent stdio proxy for the Model Context Protocol. Point it at
your real server command instead of running that command directly, and
it relays every byte exactly as before -- while recording every JSON-RPC
message to a structured log you can watch live or replay.

Right now, if an MCP integration isn't working, you're debugging blind:
no visibility into what got sent, what came back, or why a call failed.
Greenlight exists to fix that.

## Install

```bash
pip install -e .
```

(Not yet published to PyPI as `greenlight-mcp` -- install from source for now.)

## Use it

Wherever you'd normally configure a server command, wrap it:

```bash
greenlight run -- npx -y @some/mcp-server
```

instead of

```bash
npx -y @some/mcp-server
```

Every message that passes through gets logged to `./sessions/`. Watch it:

```bash
greenlight tail                 # replay the most recent session
greenlight tail -f              # follow a session that's still running
greenlight tail path/to/log.jsonl
```

Trace output is colorized by status: green for a clean success, yellow
for a slow-but-fine call, red for anything that actually failed --
including MCP tool-level failures (`result.isError`), not just
transport-level JSON-RPC errors, which are a different thing and easy to
miss if you only check for the obvious one. See `notes/day1.md` for why
that distinction mattered enough to write a whole note about it.

## How it works

`greenlight run` spawns your real server as a subprocess and sits
between it and the real MCP client, relaying stdin/stdout on two
threads. Every line is parsed as JSON-RPC, correlated by request id
(so a response knows its own method name and latency), and written to a
JSONL file. The one rule the whole thing depends on: nothing but the
child process's actual bytes ever reaches Greenlight's own stdout --
logging and UI output only ever go to stderr or to disk. A single stray
print to stdout would corrupt the protocol stream the real client is
parsing.

## Status

- [x] `greenlight run` -- transparent proxy, validated end-to-end against
      a real MCP server (not a mock)
- [x] `greenlight tail` -- live trace viewer, both static replay and
      genuine live-follow (verified separately, not assumed)
- [x] Windows PATH resolution for `npx`-style commands
- [ ] Tested against a real npx-launched server (so far only validated
      against a Python fixture server)
- [ ] HTTP/SSE transport (stdio only for now -- covers the common local
      MCP server case)
- [ ] Published to PyPI

## Notes

[`notes/`](notes/) is a running engineering log, not a cleaned-up
retrospective -- what broke, how it was found, why the fix is what it is.
