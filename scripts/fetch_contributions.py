"""Fetch the public GitHub contribution calendar — no token needed.

GitHub serves the contribution calendar as server-rendered HTML at
https://github.com/users/<username>/contributions (the same fragment the
profile page embeds). We parse the day cells and tooltips and write
data/contributions.json with raw days plus derived stats.

Usage:
    python scripts/fetch_contributions.py                 # fetch live
    python scripts/fetch_contributions.py --from-file f   # parse saved HTML (tests)
"""
import json
import re
import sys
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

USER = "Zulqarnain-10"
URL = f"https://github.com/users/{USER}/contributions"
OUT = "data/contributions.json"
UA = "Mozilla/5.0 (profile-readme-art; +https://github.com/Zulqarnain-10/Zulqarnain-10)"


def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")

    tips = {}
    for tip in soup.find_all("tool-tip"):
        tips[tip.get("for", "")] = tip.get_text(strip=True)

    count_re = re.compile(r"^([\d,]+|No)\s+contribution")
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        tip_text = tips.get(td.get("id", ""), "")
        m = count_re.match(tip_text)
        count = 0
        if m and m.group(1) != "No":
            count = int(m.group(1).replace(",", ""))
        days.append(
            {
                "date": td["data-date"],
                "count": count,
                "level": int(td.get("data-level", 0)),
            }
        )
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no day cells found — GitHub markup may have changed")

    total = sum(d["count"] for d in days)

    # sanity-check against the page's own headline number when present
    h2 = soup.find("h2")
    if h2:
        m = re.search(r"([\d,]+)\s+contributions", h2.get_text())
        if m:
            headline = int(m.group(1).replace(",", ""))
            if headline != total:
                print(f"warning: headline {headline} != summed {total}")

    streak = longest = 0
    for d in days:
        streak = streak + 1 if d["count"] > 0 else 0
        longest = max(longest, streak)
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break
    best = max(days, key=lambda d: d["count"])

    return {
        "user": USER,
        "generated": date.today().isoformat(),
        "total": total,
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "stats": {
            "current_streak": current,
            "longest_streak": longest,
            "best_day": {"date": best["date"], "count": best["count"]},
        },
        "days": days,
    }


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--from-file":
        html = open(sys.argv[2], encoding="utf-8").read()
    else:
        r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
        r.raise_for_status()
        html = r.text

    data = parse_html(html)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=0)
    s = data["stats"]
    print(
        f"{data['total']} contributions {data['range']['start']}..{data['range']['end']} | "
        f"streak {s['current_streak']}d (longest {s['longest_streak']}d) | "
        f"best {s['best_day']['date']} = {s['best_day']['count']}"
    )


if __name__ == "__main__":
    main()
