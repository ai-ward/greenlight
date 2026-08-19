"""
Greenlight CLI entry point.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional, Sequence

from greenlight.proxy import SESSIONS_DIR, run_proxy
from greenlight.render import latest_session, tail_file


def _resolve(command: list[str]) -> list[str]:
    """Resolve command[0] through PATH (and PATHEXT on Windows) before
    handing it to subprocess. Without this, `greenlight run -- npx ...`
    fails on Windows with a confusing FileNotFoundError, because
    subprocess with shell=False doesn't apply PATHEXT resolution itself
    the way a real shell would -- "npx" on Windows is actually npx.cmd."""
    if not command:
        return command
    resolved = shutil.which(command[0])
    return [resolved, *command[1:]] if resolved else command


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="greenlight",
        description="See what your MCP server is actually doing.",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    run_p = subparsers.add_parser(
        "run",
        help="Run an MCP server through the proxy, recording every message.",
    )
    run_p.add_argument("--name", default=None, help="session name (defaults to the command's name)")
    run_p.add_argument(
        "command", nargs=argparse.REMAINDER,
        help="the real MCP server command, e.g. -- npx -y @some/mcp-server",
    )

    tail_p = subparsers.add_parser(
        "tail",
        help="View a recorded session's trace -- green for ok, yellow for slow, red for failed.",
    )
    tail_p.add_argument(
        "path", nargs="?", default=None,
        help="session log to view (defaults to the most recent one in ./sessions)",
    )
    tail_p.add_argument(
        "-f", "--follow", action="store_true",
        help="keep watching for new messages, like `tail -f` (use this while a session is still running)",
    )

    args = parser.parse_args(argv)

    if args.cmd == "run":
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            parser.error("no server command given -- e.g. `greenlight run -- npx -y @some/mcp-server`")
        return run_proxy(_resolve(command), session_name=args.name)

    if args.cmd == "tail":
        path = Path(args.path) if args.path else latest_session(SESSIONS_DIR)
        if path is None:
            parser.error(f"no session logs found in {SESSIONS_DIR} -- run `greenlight run -- ...` first")
        if not path.exists():
            parser.error(f"no such file: {path}")
        tail_file(path, follow=args.follow)
        return 0

    parser.error(f"unknown command {args.cmd!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
