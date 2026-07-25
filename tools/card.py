#!/usr/bin/env python3
"""Renders the ASCII profile card into README.md between the CARD markers.

The art is value noise seeded by the current date, so it changes once a day.
No dependencies beyond the standard library.
"""

from __future__ import annotations

import datetime as dt
import math
import pathlib
import random
import re
import sys

# --- card content ------------------------------------------------------------

HEADER = "sk1gl4a"

LINES: list[tuple[str, str]] = [
    ("Role", "Informatik student"),
    ("Uni", "Leibniz Universität Hannover"),
    ("Location", "Hannover, DE"),
    ("Uptime", "{uptime} on GitHub"),
    ("", ""),
    ("Stack", "C#, Java, C, Swift"),
    ("Building", "native macOS apps, small tools"),
    ("Currently", "SwiftUI, JavaFX, Klausuren"),
    ("", ""),
    ("~ Contact", ""),
    ("Site", "sk1gl4a.dev"),
]

GITHUB_JOINED = dt.date(2020, 10, 14)

# --- art ---------------------------------------------------------------------

ART_COLS = 34
ART_ROWS = 22
RAMP = " .:-=+*#%@"
OCTAVES = 3
SCALE_X = 9.0
SCALE_Y = 4.5
WARP = 2.2
CONTRAST = 1.8  # gamma on the normalised field: higher means more empty space
FLOOR = 0.22  # everything below this stays blank


def smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


class ValueNoise:
    """Bilinear value noise with smoothstep interpolation."""

    def __init__(self, seed: int, size: int = 64) -> None:
        rng = random.Random(seed)
        self.size = size
        self.grid = [[rng.random() for _ in range(size)] for _ in range(size)]

    def at(self, x: float, y: float) -> float:
        n = self.size
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        fx, fy = smoothstep(x - x0), smoothstep(y - y0)
        g = self.grid
        a = g[y0 % n][x0 % n]
        b = g[y0 % n][(x0 + 1) % n]
        c = g[(y0 + 1) % n][x0 % n]
        d = g[(y0 + 1) % n][(x0 + 1) % n]
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(noises: list[ValueNoise], x: float, y: float) -> float:
    total, amplitude, frequency, norm = 0.0, 1.0, 1.0, 0.0
    for noise in noises:
        total += noise.at(x * frequency, y * frequency) * amplitude
        norm += amplitude
        amplitude *= 0.5
        frequency *= 2.0
    return total / norm


def render_art(seed: int) -> list[str]:
    base = [ValueNoise(seed + i * 977, 32) for i in range(OCTAVES)]
    warp = [ValueNoise(seed + 5000 + i * 331, 32) for i in range(2)]

    field: list[list[float]] = []
    for row in range(ART_ROWS):
        values: list[float] = []
        for col in range(ART_COLS):
            # characters are about twice as tall as wide, so squash y
            x = col / SCALE_X
            y = row / SCALE_Y

            wx = fbm(warp, x + 0.3, y + 1.7) - 0.5
            wy = fbm(warp, x + 4.1, y + 2.9) - 0.5
            value = fbm(base, x + WARP * wx, y + WARP * wy)

            # ridges read better than smooth clouds at this resolution
            values.append(1.0 - abs(value * 2.0 - 1.0))
        field.append(values)

    low = min(min(row) for row in field)
    high = max(max(row) for row in field)
    span = max(1e-6, high - low)

    rows: list[str] = []
    for values in field:
        chars: list[str] = []
        for value in values:
            level = (value - low) / span
            level = level**CONTRAST
            if level < FLOOR:
                chars.append(" ")
                continue
            level = (level - FLOOR) / (1.0 - FLOOR)
            chars.append(RAMP[min(len(RAMP) - 1, int(level * len(RAMP)))])
        rows.append("".join(chars).rstrip())
    return rows


# --- layout ------------------------------------------------------------------


def uptime(today: dt.date) -> str:
    months = (today.year - GITHUB_JOINED.year) * 12 + today.month - GITHUB_JOINED.month
    if today.day < GITHUB_JOINED.day:
        months -= 1
    years, rest = divmod(max(0, months), 12)
    parts = []
    if years:
        parts.append(f"{years} year" + ("s" if years != 1 else ""))
    if rest or not years:
        parts.append(f"{rest} month" + ("s" if rest != 1 else ""))
    return ", ".join(parts)


def render_info(today: dt.date) -> list[str]:
    values = {"uptime": uptime(today)}
    key_width = max(len(key) for key, _ in LINES if not key.startswith("~"))

    body: list[str] = []
    for key, value in LINES:
        if not key:
            body.append("")
        elif key.startswith("~"):
            title = key[1:].strip()
            body.append(f"{title} " + "─" * max(0, 46 - len(title)))
        else:
            filled = value.format(**values)
            dots = "." * (key_width - len(key) + 3)
            body.append(f"{key} {dots} {filled}")

    width = max(len(line) for line in body)
    head = f"{HEADER} " + "─" * max(0, width - len(HEADER) - 1)
    return [head, *body]


def render_card(today: dt.date) -> str:
    art = render_art(today.toordinal())
    info = render_info(today)

    height = max(len(art), len(info))
    art += [""] * (height - len(art))
    info += [""] * (height - len(info))

    return "\n".join(
        f"{left:<{ART_COLS}}   {right}".rstrip() for left, right in zip(art, info)
    )


# --- readme ------------------------------------------------------------------

START = "<!-- card:start -->"
END = "<!-- card:end -->"


def main() -> int:
    readme = pathlib.Path(__file__).resolve().parent.parent / "README.md"
    card = render_card(dt.date.today())

    if not readme.exists():
        print(f"{readme} not found", file=sys.stderr)
        return 1

    text = readme.read_text(encoding="utf-8")
    block = f"{START}\n\n```\n{card}\n```\n\n{END}"
    new_text, count = re.subn(
        re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S
    )
    if count == 0:
        print("card markers not found in README.md", file=sys.stderr)
        return 1

    if new_text == text:
        print("card unchanged")
        return 0

    readme.write_text(new_text, encoding="utf-8")
    print("card updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
