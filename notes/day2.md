# Greenlight — Day 2 notes

## What exists now

* `src/greenlight/render.py` -- `tail_file()`, the live trace viewer.
* `greenlight tail [path] [-f/--follow]` wired into the CLI.
* `tests/test_tail_follow.py` -- proves the `-f` flag actually follows a
  log that's still being written to, not just replays a finished one.

## Design: scrolling lines, not a redrawn table

Considered a `rich.live.Live` dashboard (a table that redraws in place)
before settling on printing each new line as it arrives, styled by
status. A live-redrawn table is the right model for a fixed-size
dashboard; a trace is unbounded and you want the scrollback (what
happened three calls ago), not just current state. Closer to `tail -f`
or `kubectl logs -f` than to `top`.

## Design: `-f` is opt-in, not default

Plain `greenlight tail` replays what's in the log and exits -- matches
how Unix `tail` actually behaves (you need `-f` to follow). Defaulting to
always-follow would be the more "impressive live demo" behavior, but it's
the less expected one, and violates it for a tool whose whole premise is
being unsurprising about what's happening.

## Verifying `-f` for real, not just trusting the code

Static replay (`greenlight tail somefile.jsonl`) is easy to convince
yourself works because you can eyeball the output once the file's done
being written. Whether `-f` actually picks up *new* lines while a session
is still open is a different, easier-to-get-wrong claim -- the polling
loop, the file handle staying valid across writes, the thread not
silently dying. `test_tail_follow.py` starts `tail_file(follow=True)` in
a background thread *while a real client session is still mid-flight*,
makes another tool call after following has already started, and asserts
that call shows up in the captured output. It does -- 4 `tools/call`
lines captured live from 2 calls made after following began.

## Status

`greenlight run` + `greenlight tail` together are now a complete loop:
record a real session, watch it live or replay it after the fact. Ran
both the original e2e test and the new follow test after wiring `tail`
into the CLI -- both still pass, nothing regressed.

## Open for next session

* No README yet. First-time visitors to the repo currently see a raw
  file listing with no context -- fine while it's just me working on it,
  not fine once this is meant to be looked at.
* Only tested against a Python fixture server so far. The Windows
  `npx`/`PATHEXT` resolution fix (`shutil.which()` in `cli.py`) is still
  unverified against an actual npx-launched MCP server -- that's the more
  realistic real-world case and hasn't been proven yet, only reasoned
  about.
* Terminal color hasn't been visually confirmed by an actual human eyeball
  in a real terminal -- only that the `rich` calls are structured
  correctly and the text/logic is right. Worth a real look before calling
  this demo-ready.
* `greenlight tail` with no path argument silently picks the most
  recently modified file in `./sessions` -- fine for a single-server demo,
  will get confusing with multiple concurrent sessions. Not a problem yet.
