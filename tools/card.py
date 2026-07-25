#!/usr/bin/env python3
"""Renders the profile card into card/dark.svg and card/light.svg.

The art is a domain-warped fractal noise field, drawn with braille glyphs:
each glyph is a 2x4 dot matrix, dot placement is ordered-dithered and the
glyph itself is shaded by the average brightness of its cell. Seeded by the
current date, so it redraws once a day. Standard library only.
"""

from __future__ import annotations

import datetime as dt
import html
import math
import pathlib

# --- content -----------------------------------------------------------------

HEADER = "sk1gl4a"

LINES: list[tuple[str, str]] = [
    ("role", "Informatik student"),
    ("uni", "Leibniz Universität Hannover"),
    ("location", "Hannover, DE"),
    ("uptime", "{uptime} on GitHub"),
    ("", ""),
    ("stack", "C#, Java, C, Swift"),
    ("site", "sk1gl4a.dev"),
]

GITHUB_JOINED = dt.date(2020, 10, 14)
SEED_SALT = "sk1gl4a"

# --- art parameters ----------------------------------------------------------

COLUMNS = 42
ROWS = 24
SCALE = 1.5
WARP = 3.6
BANDS = 2.4
CONTRAST = 2.6
OCTAVES = 4

# --- layout ------------------------------------------------------------------

FONT = "'JetBrains Mono', 'Cascadia Code', Consolas, monospace"
FONT_SIZE = 16
ROW_HEIGHT = 20
PADDING = 16
# braille glyph width varies with the viewer's fallback font, so the left
# column gets a generous reservation instead of an exact measurement
ART_CELL = 15.0
INFO_CELL = 9.9
GAP = 24

THEMES = {
    "dark": {
        "background": "#0d1117",
        "text": "#c9d1d9",
        "key": "#ffa657",
        "value": "#a5d6ff",
        "dots": "#616e7f",
        "shades": ["#1c2531", "#2d3a4a", "#3f5163", "#54687c", "#6b8095",
                   "#8399ac", "#9db1c2", "#b7c8d6", "#d3e0ea", "#eef4f9"],
    },
    "light": {
        "background": "#ffffff",
        "text": "#1f2328",
        "key": "#953800",
        "value": "#0a3069",
        "dots": "#9ba3ae",
        "shades": ["#eef1f4", "#dde3e9", "#c8d1da", "#b0bcc9", "#96a5b5",
                   "#7c8c9e", "#637386", "#4b5a6b", "#354250", "#1f2937"],
    },
}

# --- noise -------------------------------------------------------------------

MASK32 = 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    r = (a * b) & MASK32
    return r - 0x100000000 if r >= 0x80000000 else r


def _int32(x: int) -> int:
    x &= MASK32
    return x - 0x100000000 if x >= 0x80000000 else x


def hash_seed(text: str) -> int:
    h = 9
    for char in text:
        h = _int32(_imul(h, 31) + ord(char))
    return h


def mulberry32(seed: int):
    state = seed

    def rnd() -> float:
        nonlocal state
        state = _int32(state + 0x6D2B79F5)
        t = _imul(state ^ ((state & MASK32) >> 15), 1 | state)
        t = _int32(t ^ (t + _imul(t ^ ((t & MASK32) >> 7), 61 | t)))
        return ((t ^ ((t & MASK32) >> 14)) & MASK32) / 4294967296

    return rnd


def make_noise(rnd):
    size = 64
    grid = [rnd() for _ in range(size * size)]

    def at(x: int, y: int) -> float:
        return grid[((y % size) + size) % size * size + ((x % size) + size) % size]

    def noise(x: float, y: float) -> float:
        x0, y0 = math.floor(x), math.floor(y)
        tx = (x - x0) * (x - x0) * (3 - 2 * (x - x0))
        ty = (y - y0) * (y - y0) * (3 - 2 * (y - y0))
        top = at(x0, y0) + (at(x0 + 1, y0) - at(x0, y0)) * tx
        bottom = at(x0, y0 + 1) + (at(x0 + 1, y0 + 1) - at(x0, y0 + 1)) * tx
        return top + (bottom - top) * ty

    return noise


def field(today: dt.date, columns: int, rows: int) -> list[list[float]]:
    """Brightness in 0..1, sampled at `columns` x `rows` points."""
    noise = make_noise(mulberry32(hash_seed(f"{SEED_SALT}-{today.isoformat()}")))

    def fbm(x: float, y: float) -> float:
        value, amplitude, fx, fy = 0.0, 0.55, x, y
        for _ in range(OCTAVES):
            value += amplitude * noise(fx, fy)
            fx *= 2.03
            fy *= 1.97
            amplitude *= 0.5
        return value

    out = []
    for row in range(rows):
        line = []
        for col in range(columns):
            # both axes are normalised over their own sample count, which is
            # what gives the field its stretched, flowing look
            nx = ((col + 0.5) / columns) * SCALE
            ny = ((row + 0.5) / rows) * SCALE
            warped = fbm(nx + WARP * fbm(nx + 5.2, ny + 1.3),
                         ny + WARP * fbm(nx + 9.7, ny + 4.6))
            banded = 0.5 + 0.5 * math.cos(2 * math.pi * (warped * BANDS + nx * 0.35))
            line.append(banded**CONTRAST)
        out.append(line)
    return out


# --- braille -----------------------------------------------------------------

# ordered dithering: a fixed threshold per sub-pixel turns a hard cutoff into
# dot density, which is what carries the tone
BAYER = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]

# braille bit layout, column-major: dots 1-3,7 on the left, 4-6,8 on the right
DOT_BITS = [(0, 0x01), (0, 0x02), (0, 0x04), (0, 0x40),
            (1, 0x08), (1, 0x10), (1, 0x20), (1, 0x80)]


def art_cells(today: dt.date) -> list[list[tuple[str, float]]]:
    values = field(today, COLUMNS * 2, ROWS * 4)
    rows = []
    for row in range(ROWS):
        line = []
        for col in range(COLUMNS):
            bits = 0
            total = 0.0
            for index, (dx, mask) in enumerate(DOT_BITS):
                x, y = col * 2 + dx, row * 4 + index % 4
                value = values[y][x]
                total += value
                if value > (BAYER[y % 4][x % 4] + 0.5) / 16:
                    bits |= mask
            line.append((chr(0x2800 + bits), total / 8))
        rows.append(line)
    return rows


# --- info column -------------------------------------------------------------


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


def info_rows(today: dt.date) -> list[tuple[str, tuple]]:
    values = {"uptime": uptime(today)}
    key_width = max(len(key) for key, _ in LINES if key)

    rows: list[tuple[str, tuple]] = [("header", (HEADER,))]
    for key, value in LINES:
        if not key:
            rows.append(("blank", ()))
        else:
            dots = "." * (key_width - len(key) + 4)
            rows.append(("kv", (key, dots, value.format(**values))))
    return rows


# --- svg ---------------------------------------------------------------------


def build_svg(today: dt.date, theme_name: str) -> str:
    theme = THEMES[theme_name]
    shades = theme["shades"]

    info_x = PADDING + COLUMNS * ART_CELL + GAP
    rows = info_rows(today)
    info_width = max(
        len(" ".join(part for part in payload)) if kind == "kv" else 52
        for kind, payload in rows
    )
    width = round(info_x + max(info_width, 52) * INFO_CELL + PADDING)
    height = PADDING * 2 + ROWS * ROW_HEIGHT

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" '
        f'height="{height}px" font-family="{FONT}" font-size="{FONT_SIZE}px">',
        f'<rect width="{width}px" height="{height}px" '
        f'fill="{theme["background"]}" rx="15"/>',
        f'<text fill="{theme["text"]}" xml:space="preserve">',
    ]

    for index, line in enumerate(art_cells(today)):
        y = PADDING + (index + 1) * ROW_HEIGHT - 6
        spans, run, shade = [], "", None
        for glyph, brightness in line:
            current = shades[min(len(shades) - 1, int(brightness * len(shades)))]
            if current != shade and run:
                spans.append(f'<tspan fill="{shade}">{run}</tspan>')
                run = ""
            shade = current
            run += glyph
        if run:
            spans.append(f'<tspan fill="{shade}">{run}</tspan>')
        parts.append(f'<tspan x="{PADDING}" y="{y}">{"".join(spans)}</tspan>')
    parts.append("</text>")

    parts.append(f'<text fill="{theme["text"]}" xml:space="preserve">')
    for index, (kind, payload) in enumerate(rows):
        y = PADDING + (index + 1) * ROW_HEIGHT - 6
        if kind == "header":
            rule = "─" * 44
            parts.append(
                f'<tspan x="{info_x}" y="{y}">{html.escape(payload[0])} '
                f'<tspan fill="{theme["dots"]}">{rule}</tspan></tspan>'
            )
        elif kind == "kv":
            key, dots, value = payload
            parts.append(
                f'<tspan x="{info_x}" y="{y}">'
                f'<tspan fill="{theme["key"]}">{html.escape(key)}</tspan> '
                f'<tspan fill="{theme["dots"]}">{dots}</tspan> '
                f'<tspan fill="{theme["value"]}">{html.escape(value)}</tspan>'
                "</tspan>"
            )
    parts.append("</text></svg>")
    return "\n".join(parts)


def main() -> int:
    today = dt.date.today()
    out = pathlib.Path(__file__).resolve().parent.parent / "card"
    out.mkdir(exist_ok=True)

    for name in THEMES:
        (out / f"{name}.svg").write_text(build_svg(today, name), encoding="utf-8")
        print(f"card/{name}.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
