# Greenlight — Day 4 notes

## Published to PyPI

`greenlight-mcp` is live: `pip install greenlight-mcp`. Built with
`python -m build`, validated with `twine check` before upload, and --
important, not just a formality -- installed the actual built wheel into
a throwaway venv (not the dev environment) to confirm the CLI entry
point works from a real install, both before uploading and again after,
against the real PyPI index.

Token hygiene: first upload had to use an account-wide API token, since
PyPI can't scope a token to a project that doesn't exist yet. Followed up
immediately after the first successful upload: created a new token
scoped specifically to `greenlight-mcp`, swapped to it, and revoked the
account-wide one. Don't skip that step -- the account-wide token can
publish to every project on the account, not just this one.

## The demo GIF, and a dead end worth recording

Tried `vhs` (Charm's terminal-to-GIF recorder) first -- it's the right
tool for this in general, and installed cleanly via winget along with
its dependencies (`ttyd`, `ffmpeg`). But `vhs` renders by having `ttyd`
serve a web terminal and screenshotting it with a headless Chromium via
go-rod, and that browser launch hung indefinitely in this environment,
even after pointing it at an already-installed Edge via `ROD_BROWSER_BIN`
-- no browser process ever spawned, so the hang was upstream of that,
not a missing-browser problem `ROD_BROWSER_BIN` could fix.

Verified `ttyd` itself works fine in isolation (starts, binds its port,
listens) before concluding the problem was specifically in vhs's
browser-launch step and not ttyd -- didn't want to abandon the whole
approach on a guess about where it was actually stuck.

Pivoted to rendering the GIF directly with Pillow instead of recording a
real terminal: `examples/make_demo_gif.py` reads the same session log
`greenlight tail` would, and -- this part matters -- calls
`greenlight.render._format_entry` directly, the exact function the real
tool uses, rather than re-implementing the color/formatting logic a
second time for the GIF. The two can't silently drift apart, because
there's only one implementation.

`examples/demo.tape` (the vhs script) is left in the repo even though it
doesn't currently produce anything here -- it's a legitimate approach
that would work in an environment where the browser launch doesn't hang,
and there's no reason to delete correct code because this particular
environment couldn't run it.

## What's real and what's not, precisely

The GIF's *content* is entirely real: `examples/demo-session.jsonl` is an
actual recorded session (fixture server, three tool calls -- one normal,
one slow, one that fails), and the colors/text come from the tool's real
formatting function. What's not a literal screen recording is the
rendering step -- Pillow drawing text frames instead of a captured
terminal. Worth being exact about that distinction rather than letting
"real data, custom renderer" blur into "real recording."

## Status

Repo now has: working proxy, working live-follow tail UI, validated
against both a hand-built fixture and a real third-party npx server,
published and installable from PyPI, README with an accurate demo GIF.
The core "record → watch" loop this project set out to build is
complete.

## Open

* HTTP/SSE transport -- stdio only so far.
* Version bump whenever there's a real behavior change to ship; nothing
  queued right now.
