"""Terminal-style tech-stack card SVG with real brand logos.

One 860-wide card, `cat tech-stack.txt`: categories as green keys, tools as
values, each tool preceded by its brand icon (vendored simple-icons paths in
scripts/icons.json — zero network requests at view time). Tools whose brands
aren't in simple-icons get a small rounded color chip instead.

    python scripts/make_tech_stack.py [tech-stack.svg]

STATIC=1 renders a frozen frame. CSS keyframes + prefers-reduced-motion.
"""
import json
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
FG = "#c9d1d9"
KEY = "#7ee787"
GREEN = "#3fb950"
DIM = "#8b949e"

W = 860
BAR_H = 36
PAD_X = 20
LINE_H = 27
FS = 13
CH = 7.8          # forced char advance via textLength
ITEM_X = PAD_X + 16 * CH  # value column (longest key is 15 chars + 1 gap)
ICON = 13         # icon box size
ICON_GAP = 5
SEP = 16          # gap holding the separator dot

STATIC = os.environ.get("STATIC") == "1"

STACK = [
    ("Languages", ["Python", "SQL", "R", "JavaScript"]),
    ("ML / DL", ["PyTorch", "TensorFlow", "scikit-learn", "Keras", "MLflow"]),
    ("LLMs & GenAI", ["LangChain", "LlamaIndex", "OpenAI", "Anthropic", "Hugging Face"]),
    ("Data & vectors", ["Pandas", "NumPy", "FAISS", "Pinecone", "ChromaDB"]),
    ("Cloud & backend", ["AWS", "Docker", "FastAPI", "Flask", "PostgreSQL", "MongoDB"]),
]

# brands not in simple-icons -> rounded color chip
CHIP_COLORS = {
    "SQL": "#d29922",
    "OpenAI": "#10A37F",
    "LlamaIndex": "#bc8cff",
    "Pinecone": "#39c5cf",
    "ChromaDB": "#ff7b72",
    "FAISS": "#58a6ff",
    "AWS": "#FF9900",
}

T0 = 0.4
STAGGER = 0.12

ICONS = json.loads((Path(__file__).parent / "icons.json").read_text(encoding="utf-8"))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "tech-stack.svg"
    n = len(STACK) + 1  # + command line
    H = int(BAR_H + 26 + n * LINE_H + 14)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Tech stack: Python, SQL, R, JavaScript; PyTorch, TensorFlow, '
        f'scikit-learn, Keras, MLflow; LangChain, LlamaIndex, OpenAI, Anthropic, Hugging Face; '
        f'Pandas, NumPy, FAISS, Pinecone, ChromaDB; AWS, Docker, FastAPI, Flask, PostgreSQL, MongoDB">',
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

    def text_at(x, y, content, fill, bold=False, width=None):
        tl = f' textLength="{width:.0f}" lengthAdjust="spacingAndGlyphs"' if width else ""
        b = ' font-weight="bold"' if bold else ""
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" xml:space="preserve" font-family="{FONT}" '
            f'font-size="{FS}" fill="{fill}"{b}{tl}>{escape(content)}</text>'
        )

    def open_line(i):
        cls = "" if STATIC else f' class="l" style="animation-delay:{T0 + i * STAGGER:.2f}s"'
        return f"<g{cls}>"

    y0 = BAR_H + 30

    # command line
    y = y0
    p.append(open_line(0))
    p.append(text_at(PAD_X, y, "$", GREEN))
    p.append(text_at(PAD_X + 2 * CH, y, "cat tech-stack.txt", "#e6edf3", bold=True))
    p.append("</g>")

    for li, (key, items) in enumerate(STACK):
        y = y0 + (li + 1) * LINE_H
        p.append(open_line(li + 1))
        p.append(text_at(PAD_X, y, key, KEY, width=len(key) * CH))
        x = ITEM_X
        for j, item in enumerate(items):
            if j:  # separator dot
                p.append(f'<circle cx="{x + SEP / 2:.1f}" cy="{y - 4:.1f}" r="1.5" fill="{DIM}"/>')
                x += SEP
            icon = ICONS.get(item)
            if icon:
                s = ICON / 24
                p.append(
                    f'<path transform="translate({x:.1f},{y - 10.5:.1f}) scale({s:.4f})" '
                    f'fill="{icon["color"]}" d="{icon["d"]}"/>'
                )
            else:
                c = CHIP_COLORS.get(item, DIM)
                p.append(f'<rect x="{x + 1.5:.1f}" y="{y - 9:.1f}" width="10" height="10" rx="3" fill="{c}"/>')
            x += ICON + ICON_GAP
            p.append(text_at(x, y, item, FG, width=len(item) * CH))
            x += len(item) * CH
        p.append("</g>")
        if x > W - PAD_X:
            print(f"WARNING: line '{key}' overflows: ends at {x:.0f}px")

    p.append("</svg>")
    svg = "".join(p)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg) / 1024:.1f} KB, {H}px tall")


if __name__ == "__main__":
    main()
