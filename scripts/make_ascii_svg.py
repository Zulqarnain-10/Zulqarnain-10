"""Convert the prepped grayscale photo into a self-typing animated ASCII SVG.

Design choices (deliberate):
  * Monochrome — one light-gray fill; per-character rainbow is what makes
    most ASCII portraits look like static.
  * Bright -> sparse ramp with a leading space, so the white background
    prints as nothing at all.
  * Each row is wrapped in a clip that wipes left-to-right with a block
    cursor riding the edge; rows are staggered top-to-bottom. Plays once,
    then freezes (SMIL, so GitHub renders it inside <img>).

Usage:
    python scripts/make_ascii_svg.py [prepped.png] [ascii-portrait.svg]
"""
import sys
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
COLS, ROWS = 100, 60
CELL_W, CELL_H = 7.2, 12.0
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
INK = "#b9c2cc"
CURSOR = "#58a6ff"

PAD = 24
BAR_H = 36
T0 = 0.35  # s before first row starts
ROW_DUR = 0.45  # s for one row's wipe
STAGGER = 0.05  # s between row starts


GAMMA = 1.0  # >1 darkens mid-tones (highlight compression happens in prep_photo)


def to_grid(path):
    im = Image.open(path).convert("L").resize((COLS, ROWS), Image.LANCZOS)
    px = np.asarray(im).astype(float) / 255.0
    px = np.power(px, GAMMA) * 255.0
    idx = ((255 - px.astype(int)) * len(RAMP) // 256).clip(0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row) for row in idx]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    grid = to_grid(src)

    art_w, art_h = COLS * CELL_W, ROWS * CELL_H
    W = int(art_w + 2 * PAD)
    H = int(BAR_H + art_h + PAD + 12)
    ox, oy = PAD, BAR_H + 6

    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="ASCII art portrait of Syed Zulqarnain Hassan, typed in row by row">'
    )
    # terminal window
    p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="9" fill="#0d1117" stroke="#30363d"/>')
    p.append(f'<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="#21262d" stroke-width="1"/>')
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        p.append(f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2}" r="5.5" fill="{c}"/>')
    p.append(
        f'<text x="{W / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="12" fill="#8b949e">zulqarnain@github: ~/portrait</text>'
    )

    defs, body = [], []
    for r, raw in enumerate(grid):
        row = raw.rstrip()
        if not row:
            continue
        y = oy + r * CELL_H
        beg = T0 + r * STAGGER
        end = beg + ROW_DUR
        row_w = len(row) * CELL_W
        cid = f"c{r}"
        defs.append(
            f'<clipPath id="{cid}"><rect x="{ox}" y="{y}" width="0" height="{CELL_H + 1}">'
            f'<animate attributeName="width" from="0" to="{row_w:.0f}" '
            f'begin="{beg:.2f}s" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(
            f'<text x="{ox}" y="{y + CELL_H - 2.5}" clip-path="url(#{cid})" xml:space="preserve" '
            f'font-family="{FONT}" font-size="12" fill="{INK}" '
            f'textLength="{row_w:.0f}" lengthAdjust="spacingAndGlyphs">{escape(row)}</text>'
        )
        # block cursor riding the wipe edge
        body.append(
            f'<rect x="{ox}" y="{y + 1}" width="{CELL_W}" height="{CELL_H - 2}" fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{beg:.2f}s"/>'
            f'<animate attributeName="x" from="{ox}" to="{ox + row_w:.0f}" '
            f'begin="{beg:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.2f}s" fill="freeze"/></rect>'
        )

    p.append("<defs>" + "".join(defs) + "</defs>")
    p.extend(body)
    p.append("</svg>")

    svg = "".join(p)
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg) / 1024:.0f} KB, {sum(1 for g in grid if g.strip())} rows")


if __name__ == "__main__":
    main()
