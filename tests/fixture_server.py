"""
A small, real MCP server, built on the official SDK, used to validate the
proxy against actual protocol traffic instead of a hand-rolled mock.

    add(a, b) -> a + b                     -- the boring happy path
    slow_echo(text, delay_ms) -> text      -- exercises latency tracking
    boom() -> raises                       -- exercises error-path logging
"""
from mcp.server.mcpserver import MCPServer

server = MCPServer("greenlight-fixture")


@server.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@server.tool()
def slow_echo(text: str, delay_ms: int = 200) -> str:
    """Echo text back after a delay, in milliseconds."""
    import time
    time.sleep(delay_ms / 1000)
    return text


@server.tool()
def boom() -> str:
    """Always raises, to exercise the proxy's error-path logging."""
    raise RuntimeError("this tool always fails, on purpose")


if __name__ == "__main__":
    import sys
    # Default: stdio, used by the stdio proxy tests. Pass "streamable-http"
    # and a port to run the same tool definitions over HTTP instead, for
    # the HTTP proxy tests -- one set of tools, not two copies to drift
    # apart.
    if len(sys.argv) > 1 and sys.argv[1] == "streamable-http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
        server.run(transport="streamable-http", port=port)
    else:
        server.run()
