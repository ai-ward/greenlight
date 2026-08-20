"""
Renders examples/demo-session.jsonl into examples/demo.gif.

Reuses greenlight.render._format_entry directly -- the exact same
function `greenlight tail` calls -- so the GIF is guaranteed to show
literally what the tool produces, not a hand-copied approximation that
could quietly drift out of sync with the real output.

Renders frames with Pillow instead of recording a real terminal (vhs's
headless-Chromium screenshot pipeline hung indefinitely trying to launch
a browser in this environment -- see notes/day4.md). The content and
colors are 100% real, pulled from an actual recorded session; only the
rendering mechanism is a stand-in for a literal screen capture.

Usage:
    .venv\\Scripts\\python.exe examples\\make_demo_gif.py
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from greenlight.render import _format_entry  # noqa: E402

LOG_PATH = ROOT / "examples" / "demo-session.jsonl"
OUT_PATH = ROOT / "examples" / "demo.gif"

FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
FONT_SIZE = 24
BG = (40, 42, 54)          # Dracula-ish background
FG_DEFAULT = (248, 248, 242)
COLORS = {
    "white": (248, 248, 242),
    "dim": (98, 114, 164),
    "green": (80, 250, 123),
    "yellow": (241, 250, 140),
    "bold red": (255, 85, 85),
}
PADDING = 24
LINE_HEIGHT = int(FONT_SIZE * 1.55)
WIDTH = 1000
HOLD_FRAMES_PER_LINE = 5   # repeats of the "just appeared" frame, for readable pacing
FRAME_MS = 220


def load_lines() -> list[tuple[str, str]]:
    header = [
        ("  .-----.", "white"),
        ("  |  o  |", "bold red"),
        ("  |  o  |", "yellow"),
        ("  |  o  |", "green"),
        ("  '-----'", "white"),
        ("  greenlight", "white"),
        ("", "white"),
        (f"watching {LOG_PATH.name}", "white"),
        ("-> client to server   <- server to client", "dim"),
        ("", "white"),
    ]
    trace = []
    for line in LOG_PATH.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        text, style = _format_entry(entry)
        trace.append((text, style))
    return header + trace


def render_frame(lines: list[tuple[str, str]], font: ImageFont.FreeTypeFont) -> Image.Image:
    height = PADDING * 2 + LINE_HEIGHT * max(len(lines), 1)
    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    for text, style in lines:
        color = COLORS.get(style, FG_DEFAULT)
        draw.text((PADDING, y), text, font=font, fill=color)
        y += LINE_HEIGHT
    return img


HEADER_LINE_COUNT = 10  # banner + "watching..." + arrow legend + blank


def main() -> None:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    all_lines = load_lines()

    final_height = PADDING * 2 + LINE_HEIGHT * len(all_lines)
    frames: list[Image.Image] = []

    # Header appears instantly, held briefly -- nobody needs to watch a
    # static banner "type out" one line at a time. Only the actual trace
    # (the part that's the point of the demo) animates in.
    header_canvas = Image.new("RGB", (WIDTH, final_height), BG)
    header_canvas.paste(render_frame(all_lines[:HEADER_LINE_COUNT], font), (0, 0))
    for _ in range(HOLD_FRAMES_PER_LINE * 3):
        frames.append(header_canvas)

    for n in range(HEADER_LINE_COUNT + 1, len(all_lines) + 1):
        canvas = Image.new("RGB", (WIDTH, final_height), BG)
        frame = render_frame(all_lines[:n], font)
        canvas.paste(frame, (0, 0))
        for _ in range(HOLD_FRAMES_PER_LINE):
            frames.append(canvas)

    # hold the final, complete frame longer so it's readable before looping
    for _ in range(HOLD_FRAMES_PER_LINE * 6):
        frames.append(frames[-1])

    frames[0].save(
        OUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
    )
    print(f"wrote {OUT_PATH} ({len(frames)} frames, {OUT_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
