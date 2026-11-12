#!/usr/bin/env python3
"""Usage: python bubbles.py sheet.csv [--tags] [--tag NAME] [--problems-only] [--top N] [--out FILE.svg]"""

import argparse
import csv
import math
import re
import sys
from collections import Counter

NON_PROBLEM = {"no problem", "download help/how to"}

STOP = set("""
a about after again all also am an and any are aren't as at be because been before being but by can can't could
did didn't do does doesn't doing don't down for from get got had has have haven't having he her here hers him his
how i i'm i've if in into is isn't it it's its just like me more most my no not now of on once one only or other our
out over really same she should so some such than that the their them then there these they this those through to
too under up us very want was wasn't we were what when where which while who why will with would you your yours
im ive dont cant didnt doesnt isnt wont thats theres anyone anything know think thing things still even much many
use used using find looking look need help please thanks thank hi hello hey im im anyone someone ok okay also
lol yes yeah make made going go gone back new way ago been better good first two three
sims sim sims4 game mod mods cc image https http www com reddit post posts time lot something since else content stuff
everyone everything people getting trying tried found sure another recently few start see off id i'd it'd
""".split())

PALETTE = ["#7b61ff", "#00a878", "#ff6b6b", "#f5a623", "#2d9cdb", "#c05cc9", "#4bb543", "#e8590c"]
TAG_COLORS = {
    "Malware/virus scare": "#e03131", "Account/info theft": "#c2255c", "Scam/fake download page": "#e8590c",
    "Phishing/social engineering": "#9c36b5", "Corrupted/broken save": "#1971c2",
    "Game errors/conflicts": "#0c8599", "Download help/how to": "#2f9e44", "No problem": "#868e96",
}


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    for i, r in enumerate(rows):
        low = [c.strip().lower() for c in r]
        if "title" in low and ("content" in low or "issue type" in low):
            head = low
            out = []
            for r2 in rows[i + 1:]:
                if not any(c.strip() for c in r2):
                    continue
                out.append({head[j]: r2[j] for j in range(min(len(head), len(r2)))})
            return out
    sys.exit("Couldn't find a header row with 'Title' in it. Check your CSV.")


def tags_of(r):
    return [t.strip() for t in (r.get("issue type") or "").split(",") if t.strip()]


def words(text):
    text = re.sub(r"https?://\S+", " ", text.lower().replace("’", "'"))
    for w in re.findall(r"[a-z][a-z'/\-]{2,}", text):
        w = w.strip("'-/")
        if len(w) >= 3 and w not in STOP:
            yield w


def pack(items, width, height):
    mx = max(c for _, c in items)
    rmax = min(width, height) * 0.16
    placed = []
    for label, c in sorted(items, key=lambda x: -x[1]):
        r = max(16, rmax * math.sqrt(c / mx))
        a, d = 0.0, 0.0
        while True:
            x = width / 2 + d * math.cos(a)
            y = height / 2 + d * math.sin(a) * 0.75
            if all((x - px) ** 2 + (y - py) ** 2 >= (r + pr + 3) ** 2 for _, _, px, py, pr in placed):
                placed.append((label, c, x, y, r))
                break
            a += 0.35
            d += 0.9 * 0.35 / (2 * math.pi) * 10
    minx = min(x - r for _, _, x, _, r in placed); maxx = max(x + r for _, _, x, _, r in placed)
    miny = min(y - r for _, _, _, y, r in placed); maxy = max(y + r for _, _, _, y, r in placed)
    s = min((width - 40) / (maxx - minx), (height - 40) / (maxy - miny))
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    return [(l, c, width / 2 + (x - cx) * s, height / 2 + (y - cy) * s, r * s) for l, c, x, y, r in placed]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(placed, title, colorfn):
    W, H = 1200, 800
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="Segoe UI, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="24" y="36" font-size="22" font-weight="700" fill="#222">{esc(title)}</text>']
    for i, (label, c, x, y, r) in enumerate(placed):
        col = colorfn(label, i)
        fs = max(9, min(r * 0.42, 15 + r * 0.18, (r * 1.7) / max(len(label), 1) * 1.55))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" fill-opacity="0.85"/>')
        out.append(f'<text x="{x:.1f}" y="{y - 2:.1f}" text-anchor="middle" font-size="{fs:.1f}" '
                   f'font-weight="600" fill="#fff">{esc(label)}</text>')
        out.append(f'<text x="{x:.1f}" y="{y + fs * 0.95:.1f}" text-anchor="middle" font-size="{fs * 0.8:.1f}" '
                   f'fill="#fff" fill-opacity="0.9">{c}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description="Make a bubble picture from your coded CSV.")
    p.add_argument("csv")
    p.add_argument("--tag", help='only posts with this Issue Type, e.g. "Malware/virus scare"')
    p.add_argument("--problems-only", action="store_true", help='skip "No problem" and "Download help/how to" posts')
    p.add_argument("--tags", action="store_true", help="one bubble per Issue Type instead of words")
    p.add_argument("--top", type=int, default=50, help="how many words to show (default 50)")
    p.add_argument("--out", help="output .svg file")
    a = p.parse_args()

    rows = read_rows(a.csv)
    base = re.sub(r"\.csv$", "", a.csv, flags=re.I)

    if a.tags:
        counts = Counter(t for r in rows for t in (tags_of(r) or ["(blank)"]))
        items = list(counts.items())
        placed = [(l, c, x, y + 30, r) for l, c, x, y, r in pack(items, 1200, 740)]
        out = a.out or base + "_tags.svg"
        open(out, "w", encoding="utf-8").write(
            svg(placed, f"Posts per Issue Type (n={len(rows)} posts; a post with 2 tags counts in both)", lambda l, i: TAG_COLORS.get(l, "#868e96")))
        print(f"Saved {out}")
        return

    sel = rows
    label = "all posts"
    if a.tag:
        sel = [r for r in rows if a.tag.strip().lower() in [t.lower() for t in tags_of(r)]]
        label = a.tag
    elif a.problems_only:
        sel = [r for r in rows if any(t.lower() not in NON_PROBLEM for t in tags_of(r))]
        label = "problem posts only"
    if not sel:
        sys.exit("No posts matched. Check the tag spelling against your Issue Type column.")

    counter = Counter()
    for r in sel:
        counter.update(set(words((r.get("title") or "") + " " + (r.get("content") or ""))))
    items = counter.most_common(a.top)
    placed = [(l, c, x, y + 30, r) for l, c, x, y, r in pack(items, 1200, 740)]
    out = a.out or base + "_words.svg"
    open(out, "w", encoding="utf-8").write(
        svg(placed, f"Most common words: {label} (n={len(sel)} posts; number = posts mentioning it)",
            lambda l, i: PALETTE[i % len(PALETTE)]))
    print(f"Saved {out}  ({len(sel)} posts)")
    print("Top words:", ", ".join(f"{w} ({c})" for w, c in items[:15]))


if __name__ == "__main__":
    main()