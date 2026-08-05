"""Terminal-style tech-stack card SVG — replaces the shields.io badge wall.

One 860-wide card, `cat tech-stack.txt`, categories as green keys and tools
as values, printed line by line. Keeping this self-generated (instead of 25
shields.io badges) makes the README's 'no third-party image services' claim
literally true and keeps every color on the terminal palette.

    python scripts/make_tech_stack.py [tech-stack.svg]

STATIC=1 renders a frozen frame. CSS keyframes + prefers-reduced-motion.
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

W = 860
BAR_H = 36
PAD_X = 20
LINE_H = 21.5
FS = 13
KEY_W = 15  # key column width in characters

STATIC = os.environ.get("STATIC") == "1"

# (key, [items]) — first item of each row is the core tool, tinted blue
STACK = [
    ("Languages", ["Python", "SQL", "R", "JavaScript"]),
    ("ML / DL", ["PyTorch", "TensorFlow", "scikit-learn", "Keras", "MLflow"]),
    ("LLMs & GenAI", ["LangChain", "LlamaIndex", "OpenAI", "Anthropic", "Hugging Face"]),
    ("Vector stores", ["FAISS", "Pinecone", "ChromaDB"]),
    ("Cloud & data", ["AWS", "Docker", "FastAPI", "Flask", "PostgreSQL", "MongoDB", "Pandas", "NumPy"]),
]

T0 = 0.4
STAGGER = 0.12


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "tech-stack.svg"
    n = len(STACK) + 1  # + command line
    H = int(BAR_H + 26 + n * LINE_H + 20)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Tech stack: Python, SQL, PyTorch, TensorFlow, LangChain, OpenAI, '
        f'FAISS, Pinecone, AWS, Docker and more">',
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

    def emit(i, spans):
        y = BAR_H + 26 + i * LINE_H
        cls = "" if STATIC else f' class="l" style="animation-delay:{T0 + i * STAGGER:.2f}s"'
        p.append(
            f'<text{cls} x="{PAD_X}" y="{y}" xml:space="preserve" font-family="{FONT}" '
            f'font-size="{FS}" fill="{FG}">{spans}</text>'
        )

    emit(0, f'<tspan fill="{GREEN}">$ </tspan><tspan fill="#e6edf3" font-weight="bold">cat tech-stack.txt</tspan>')
    for i, (key, items) in enumerate(STACK):
        pad = " " * max(1, KEY_W - len(key))
        sep = f'<tspan fill="{DIM}"> · </tspan>'
        vals = sep.join(
            f'<tspan fill="{BLUE if j == 0 else FG}">{escape(item)}</tspan>'
            for j, item in enumerate(items)
        )
        emit(i + 1, f'<tspan fill="{KEY}">{escape(key)}</tspan><tspan>{escape(pad)}</tspan>{vals}')

    p.append("</svg>")
    svg = "".join(p)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg) / 1024:.1f} KB, {H}px tall")


if __name__ == "__main__":
    main()
