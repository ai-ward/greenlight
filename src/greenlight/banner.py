"""
The banner. Purely cosmetic -- never called from run_proxy(), which has
to keep stdout pure JSON-RPC and shouldn't spam stderr with art on every
host-triggered startup. This only shows up where a human actually typed
the command: bare `greenlight` and `greenlight tail`.
"""
from rich.console import Console

_LINES = [
    ("  .-----.", "white"),
    ("  |  o  |", "bold red"),
    ("  |  o  |", "bold yellow"),
    ("  |  o  |", "bold green"),
    ("  '-----'", "white"),
]


def print_banner(console: Console) -> None:
    for text, style in _LINES:
        console.print(text, style=style, highlight=False)
    console.print("  greenlight", style="bold", highlight=False)
    console.print()
