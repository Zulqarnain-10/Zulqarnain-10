"""Hand-authored neofetch-style info card SVG.

A terminal window that 'prints' key/value rows about the owner, each line
fading + sliding in on a short stagger, with a blinking block cursor at the
end. Identity + proof only — the tech stack and projects have their own
cards, so nothing here repeats them. Edit LINES below when details change,
then re-run:

    python scripts/make_info_card.py [info-card.svg]

STATIC=1 renders a frozen frame (no animation) for previews.
Animation is CSS keyframes (same technique as the heatmap) so
prefers-reduced-motion users get the finished card instantly.
"""
import os
import sys
from xml.sax.saxutils import escape

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
FG = "#c9d1d9"
KEY = "#7ee787"
GREEN = "#3fb950"
BLUE = "#58a6ff"
DIM = "#8b949e"

W = 490
BAR_H = 36
PAD_X = 20
LINE_H = 27.4  # airy spacing; keeps the card's height matched to the portrait
FS = 13

KEY_W = 11  # key column width in characters

STATIC = os.environ.get("STATIC") == "1"

# (key, value, value_color) — key "$" -> command line, "" -> continuation
LINES = [
    ("$", "whoami --verbose", None),
    ("Name:", "Syed Zulqarnain Hassan", None),
    ("Role:", "AI/ML Engineer · Data Scientist", None),
    ("Base:", "New York", None),
    ("Degrees:", "M.S. Data Science — NYIT '26 · 3.86 GPA", None),
    ("", "B.S. Computer Engineering — FAST-NUCES '24", None),
    ("Award:", "Data Science Graduate Achievement Award", None),
    ("Founder:", "Altechra — AI software agency", None),
    ("Shipped:", "38+ client AI/ML projects · Top Rated", None),
    ("Contact:", "linkedin.com/in/syedzulqarnainh", BLUE),
    ("Status:", "open to DS · ML · AI roles", GREEN),
]

PALETTE = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"]

# The portrait finishes typing at ~2.1s; the card starts answering at 1.9s
# so the choreography reads portrait-types -> card-responds.
T0 = 1.9
STAGGER = 0.09


def line_svg(i, key, val, val_color):
    y = BAR_H + 26 + i * LINE_H
    beg = T0 + i * STAGGER
    if key == "$":
        spans = (
            f'<tspan fill="{GREEN}">$ </tspan>'
            f'<tspan fill="#e6edf3" font-weight="bold">{escape(val)}</tspan>'
        )
    elif key == "":  # continuation line — value aligned under the one above
        spans = f'<tspan fill="{val_color or FG}">{escape(" " * KEY_W + val)}</tspan>'
    else:
        pad = " " * max(1, KEY_W - len(key))
        spans = (
            f'<tspan fill="{KEY}">{escape(key)}</tspan>'
            f'<tspan fill="{val_color or FG}">{escape(pad + val)}</tspan>'
        )
    cls = "" if STATIC else f' class="l" style="animation-delay:{beg:.2f}s"'
    return (
        f'<text{cls} x="{PAD_X}" y="{y}" xml:space="preserve" font-family="{FONT}" '
        f'font-size="{FS}" fill="{FG}">{spans}</text>'
    )


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    n = len(LINES)
    pal_y = BAR_H + 26 + n * LINE_H + 6
    H = int(pal_y + 14 + 22)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Terminal card: Syed Zulqarnain Hassan — AI/ML Engineer and Data Scientist, Dix Hills NY">',
    ]
    if not STATIC:
        p.append(
            "<style>"
            ".l{opacity:0;animation:in .35s ease-out forwards}"
            "@keyframes in{from{opacity:0;transform:translateX(10px)}to{opacity:1;transform:none}}"
            "@media (prefers-reduced-motion:reduce){.l{animation:none;opacity:1;transform:none}}"
            "</style>"
        )
    p.extend([
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="9" fill="#0d1117" stroke="#30363d"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="#21262d"/>',
    ])
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        p.append(f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2}" r="5.5" fill="{c}"/>')
    p.append(
        f'<text x="{W / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="12" fill="{DIM}">zulqarnain@github: ~</text>'
    )

    for i, (k, v, c) in enumerate(LINES):
        p.append(line_svg(i, k, v, c))

    # palette dots
    beg = T0 + n * STAGGER
    dots = "".join(
        f'<rect x="{PAD_X + i * 22}" y="{pal_y}" width="14" height="14" rx="3" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    cls = "" if STATIC else f' class="l" style="animation-delay:{beg:.2f}s"'
    p.append(f'<g{cls}>{dots}</g>')

    # blinking cursor after the palette
    cx = PAD_X + len(PALETTE) * 22 + 6
    if STATIC:
        p.append(f'<rect x="{cx}" y="{pal_y}" width="8" height="14" fill="{FG}"/>')
    else:
        p.append(
            f'<rect x="{cx}" y="{pal_y}" width="8" height="14" fill="{FG}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.49;0.5;0.99;0.995;1" '
            f'begin="{beg + 0.4:.2f}s" dur="1.2s" repeatCount="indefinite"/></rect>'
        )
    p.append("</svg>")

    svg = "".join(p)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg) / 1024:.1f} KB, {H}px tall ({n} lines)")


if __name__ == "__main__":
    main()
