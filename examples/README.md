# examples/

- `demo-session.jsonl` -- a real recorded session (fixture server: one
  normal call, one slow call, one that fails). This is what the README's
  GIF is built from.
- `make_demo_gif.py` -- regenerates `demo.gif` from that session log,
  using the actual `greenlight.render` formatting code, not a
  reimplementation of it.
- `demo.tape` -- a `vhs` script that would record a real terminal session
  instead. Didn't work in this environment (see `notes/day4.md` for why
  -- a headless-Chromium hang, not a bug in the script), left in as a
  legitimate alternative approach for an environment where it does.

Regenerate the GIF:

```bash
.venv\Scripts\python.exe examples\make_demo_gif.py
```
