"""Render data/contributions.json as an animated terminal-style heatmap SVG.

The classic 53-week x 7-day calendar of rounded boxes on a GitHub-green
ramp (plus a neon top end for standout days), revealed once with a
diagonal line-after-line slide, then frozen. Month labels, weekday labels,
a Less->More legend, and a stats footer. CSS keyframes only — plays when
GitHub renders the SVG via <img>.

Usage:
    python scripts/render_heatmap_svg.py [contrib-heatmap.svg]
"""
import json
import sys
from datetime import datetime

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#           none      L1         L2         L3         L4         L5: neon top end

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
DIM = "#8b949e"
FG = "#c9d1d9"
GREEN = "#3fb950"

W = 860
BAR_H = 36
PAD = 20
LABEL_W = 30  # weekday label gutter
CELL = 11.0
GAP = 3.5
PITCH = CELL + GAP
T0 = 0.4
DIAG = 0.02  # s per diagonal step
DUR = 0.32


def level_of(day, max_count):
    lv = day["level"]
    if lv >= 4 and max_count > 0 and day["count"] >= 0.85 * max_count:
        return 5
    return lv


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "contrib-heatmap.svg"
    data = json.load(open("data/contributions.json"))
    days = data["days"]
    max_count = max(d["count"] for d in days)

    # column/row placement: GitHub weeks start on Sunday
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    lead = (first.weekday() + 1) % 7  # weekday(): Mon=0 ... Sun=6 -> Sun=0
    cells = []
    months = {}  # col -> "Aug"
    for i, d in enumerate(days):
        idx = i + lead
        col, row = divmod(idx, 7)
        dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
        if dt.day <= 7 and col not in months and row == 0 or (dt.day == 1):
            months.setdefault(col, dt.strftime("%b"))
        cells.append((col, row, d))
    ncols = cells[-1][0] + 1

    gx = PAD + LABEL_W
    gy = BAR_H + 34  # room for month labels
    grid_w = ncols * PITCH - GAP
    H = int(gy + 7 * PITCH - GAP + 46)
    total_w = int(gx + grid_w + PAD)
    ox = (W - total_w) // 2  # center if narrower than W

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{data["total"]:,} GitHub contributions in the last year, drawn as an animated heatmap">',
        "<style>"
        f".d{{opacity:0;animation:in {DUR}s ease-out forwards}}"
        "@keyframes in{from{opacity:0;transform:translateY(-7px)}to{opacity:1;transform:none}}"
        f".f{{opacity:0;animation:fade .5s ease-out forwards}}"
        "@keyframes fade{to{opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.d,.f{animation:none;opacity:1;transform:none}}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="9" fill="#0d1117" stroke="#30363d"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="#21262d"/>',
    ]
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        p.append(f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2}" r="5.5" fill="{c}"/>')
    p.append(
        f'<text x="{W / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="12" fill="{DIM}">zulqarnain@github: ~</text>'
    )

    # month labels (skip labels that would crowd the previous one)
    last_x = -1e9
    for col in sorted(months):
        x = ox + gx + col * PITCH
        if x - last_x >= 44:
            p.append(
                f'<text class="f" style="animation-delay:{T0:.2f}s" x="{x}" y="{gy - 10}" '
                f'font-family="{FONT}" font-size="11" fill="{DIM}">{months[col]}</text>'
            )
            last_x = x

    # weekday labels
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(
            f'<text class="f" style="animation-delay:{T0:.2f}s" x="{ox + PAD}" '
            f'y="{gy + row * PITCH + CELL - 2}" font-family="{FONT}" font-size="10" fill="{DIM}">{name}</text>'
        )

    # day cells, diagonal reveal
    for col, row, d in cells:
        delay = T0 + (col + row) * DIAG
        p.append(
            f'<rect class="d" style="animation-delay:{delay:.2f}s" '
            f'x="{ox + gx + col * PITCH:.1f}" y="{gy + row * PITCH:.1f}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[level_of(d, max_count)]}">'
            f'<title>{d["count"]} on {d["date"]}</title></rect>'
        )

    tail = T0 + (ncols + 6) * DIAG + DUR
    fy = gy + 7 * PITCH - GAP + 26

    s = data["stats"]
    best_dt = datetime.strptime(s["best_day"]["date"], "%Y-%m-%d").date()
    # a dead current streak is not a stat worth advertising — show the daily
    # average instead whenever the streak is 0
    if s["current_streak"] > 0:
        mid_stat = f'{s["current_streak"]}d streak'
    else:
        mid_stat = f'avg {data["total"] / max(1, len(days)):.1f}/day'
    stats_text = (
        f'<tspan fill="{GREEN}" font-weight="bold">{data["total"]:,}</tspan>'
        f'<tspan fill="{FG}"> contributions in the last year</tspan>'
        f'<tspan fill="{DIM}">  ·  {mid_stat}  ·  '
        f'{s["longest_streak"]}d longest  ·  best {best_dt.strftime("%b")} {best_dt.day}: '
        f'{s["best_day"]["count"]}</tspan>'
    )
    p.append(
        f'<text class="f" style="animation-delay:{tail:.2f}s" x="{ox + PAD}" y="{fy}" '
        f'font-family="{FONT}" font-size="12">{stats_text}</text>'
    )

    # legend: Less -> More
    lx = ox + gx + grid_w - 6 * 15 - 74
    p.append(
        f'<g class="f" style="animation-delay:{tail:.2f}s">'
        f'<text x="{lx - 34}" y="{fy}" font-family="{FONT}" font-size="11" fill="{DIM}">Less</text>'
        + "".join(
            f'<rect x="{lx + i * 15}" y="{fy - 9}" width="11" height="11" rx="2.5" fill="{c}"/>'
            for i, c in enumerate(PALETTE)
        )
        + f'<text x="{lx + 6 * 15 + 6}" y="{fy}" font-family="{FONT}" font-size="11" fill="{DIM}">More</text></g>'
    )
    p.append("</svg>")

    svg = "".join(p)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}: {len(svg) / 1024:.0f} KB, {ncols} weeks, max {max_count}")


if __name__ == "__main__":
    main()
