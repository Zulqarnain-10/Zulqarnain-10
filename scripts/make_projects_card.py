"""Terminal-style flagship-projects card SVG — an 'ls -la' that delivers.

One 860-wide card: each project prints as a directory row (permissions,
name, stack) with an indented description line carrying the headline
metric in green. Links can't live inside an <img>, so the README keeps a
small <sub> link row right under the card.

    python scripts/make_projects_card.py [projects.svg]

STATIC=1 renders a frozen frame. CSS keyframes + prefers-reduced-motion.
"""
import os
import sys
from xml.sax.saxutils import escape

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
FG = "#c9d1d9"
GREEN = "#3fb950"
KEY = "#7ee787"
BLUE = "#58a6ff"
DIM = "#8b949e"

W = 860
BAR_H = 36
PAD_X = 20
LINE_H = 21.5
FS = 13
NAME_W = 22  # name column width in characters

STATIC = os.environ.get("STATIC") == "1"

# (dirname, stack, description, metric)
PROJECTS = [
    (
        "jobcraft/",
        "LangChain · OpenAI · FAISS · Streamlit",
        "AI job-search agent — resume analysis, matching, interview prep",
        "85% match accuracy",
    ),
    (
        "medbot-rag/",
        "LangChain · Pinecone · Flask",
        "Medical Q&A grounded in trusted references via RAG",
        "94% query accuracy",
    ),
    (
        "material-classifier/",
        "TensorFlow · Keras · Raspberry Pi",
        "CNN + sensor-fusion recycling sorter, PEC-funded capstone",
        "96% accuracy",
    ),
]

T0 = 0.4
STAGGER = 0.14


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "projects.svg"
    n = 1 + 2 * len(PROJECTS)
    H = int(BAR_H + 26 + n * LINE_H + 20)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Flagship projects: JobCraft (85% match accuracy), MedBot RAG '
        f'(94% query accuracy), Material Classifier (96% accuracy)">',
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

    emit(0, f'<tspan fill="{GREEN}">$ </tspan><tspan fill="#e6edf3" font-weight="bold">ls -la ./projects</tspan>')
    for i, (name, stack, desc, metric) in enumerate(PROJECTS):
        pad = " " * max(1, NAME_W - len(name))
        emit(
            1 + 2 * i,
            f'<tspan fill="{DIM}">drwxr-xr-x  </tspan>'
            f'<tspan fill="{KEY}" font-weight="bold">{escape(name)}</tspan>'
            f'<tspan>{escape(pad)}</tspan><tspan fill="{BLUE}">{escape(stack)}</tspan>',
        )
        emit(
            2 + 2 * i,
            f'<tspan fill="{DIM}">            └─ {escape(desc)} · </tspan>'
            f'<tspan fill="{GREEN}">{escape(metric)}</tspan>',
        )

    p.append("</svg>")
    svg = "".join(p)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg) / 1024:.1f} KB, {H}px tall")


if __name__ == "__main__":
    main()
