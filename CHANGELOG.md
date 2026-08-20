# Changelog

## 0.2.0

- `greenlight run --http <url>` -- proxy a remote Streamable HTTP MCP
  server, not just stdio. Same session log format either way; `tail`
  and `stats` work on it unmodified.
- `greenlight stats [path] [--json]` -- message counts, latency
  (min/median/max, per method), and a pass/fail verdict. Exits non-zero
  on any failure (transport or tool-level), so it's usable as a CI
  check, not just an interactive summary.
- Validated against a real npx-launched third-party server (the
  official MCP reference server) in addition to the Python fixture used
  in 0.1.0.

## 0.1.0

- `greenlight run -- <command>` -- transparent stdio proxy for MCP
  servers. Relays stdin/stdout exactly, logs every JSON-RPC message to
  a structured JSONL file.
- `greenlight tail [path] [-f]` -- live trace viewer, colorized by
  status (green/yellow/red), both static replay and live-follow.
- Distinguishes transport-level JSON-RPC errors from MCP tool-level
  failures (`result.isError`) -- the latter is not `"error" in msg` and
  is easy to miss if you only check for the obvious kind.
