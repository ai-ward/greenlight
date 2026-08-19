"""
Greenlight CLI entry point.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from typing import Optional, Sequence

from greenlight.proxy import run_proxy


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

    args = parser.parse_args(argv)

    if args.cmd == "run":
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            parser.error("no server command given -- e.g. `greenlight run -- npx -y @some/mcp-server`")
        return run_proxy(_resolve(command), session_name=args.name)

    parser.error(f"unknown command {args.cmd!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
