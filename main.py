#!/usr/bin/env python3
"""Usage: python csv_tagger.py posts.csv [--out FILE] [--fill-tags] | --selftest"""

import argparse
import csv
import re
import sys
from urllib.parse import urlparse

TAGS = {
    "Malware/virus scare": {
        "kind": "security",
        "strong": [
            r"\bvirus(?:es)?\b", r"\bmalware\b", r"\btrojans?\b", r"\bmalwarebytes\b",
            r"\bwindows defender\b", r"\banti-?virus\b", r"\bkeyloggers?\b", r"\bspyware\b",
            r"\bransomware\b", r"\badware\b", r"\.exe\b", r"\bexecutables?\b",
            r"\bsuspicious (?:file|download|link|site|website)s?\b",
        ],
        "weak": [r"\binstallers?\b", r"\bquarantine[ds]?\b", r"\bflagged\b"],
    },
    "Account/info theft": {
        "kind": "security",
        "strong": [
            r"\bhacked\b", r"\bcompromised\b",
            r"\baccount (?:was |got |has been )?(?:hacked|stolen|compromised)\b",
            r"\bstolen (?:account|password|info|information|data|login|token)s?\b",
            r"\basked for my (?:info|information|password|login|email)\b",
            r"\bpassword (?:stolen|leaked|was changed)\b",
        ],
        "weak": [r"\bpasswords?\b", r"\blogin\b", r"\blog in\b", r"\btokens?\b", r"\bstolen\b"],
    },
    "Scam/fake download page": {
        "kind": "security",
        "strong": [
            r"\bfake download(?: button| page| link| site)?s?\b", r"\bpop-?ups?\b",
            r"\bredirect(?:s|ed|ing)?\b", r"\blink ?shorteners?\b", r"\badf\.?ly\b",
            r"\blinkvertise\b", r"\bsurvey ?walls?\b", r"\bdownload managers?\b",
            r"\bcaptcha loops?\b", r"\bscam(?:s|my|med|mers?)?\b",
            r"\b(?:took|taken|sent|transferred|brought|moved|opened)\b(?: me| my browser)?"
            r"(?: automatically)? (?:to|into)? ?(?:a |an |some )?"
            r"(?:random |weird |sketchy |crypto |different |new |unknown )?(?:website|site|page|tab)\b",
            r"\bcrypto (?:website|site|page)\b",
        ],
        "weak": [r"\bads?\b", r"\bcaptcha\b", r"\bfake\b", r"\bsketchy\b", r"\bshady\b"],
    },
    "Phishing/social engineering": {
        "kind": "security",
        "strong": [
            r"\bphishing\b", r"\bfake patreon\b", r"\bimperson(?:ate|ates|ated|ating|ation|ator)\b",
            r"\bgiveaways?\b", r"\bsocial engineering\b",
            r"\bverify (?:your|my) (?:account|email|identity)\b",
        ],
        "weak": [r"\bdms?\b", r"\bfree\b", r"\bearly access\b", r"\bverify\b"],
    },
    "Corrupted/broken save": {
        "kind": "technical",
        "strong": [
            r"\bcorrupt(?:ed|ion)?\b", r"\bwiped\b",
            r"\bsave (?:broke|broken|won't load|is gone|got wiped|was wiped|deleted)\b",
            r"\bsave ?files? (?:broke|broken|gone|wiped|missing)\b",
            r"\blost (?:my|all my|the) saves?\b", r"\bmy save is gone\b", r"\bsave gone\b",
        ],
        "weak": [r"\bgone\b", r"\bdisappeared\b", r"\bmissing\b"],
    },
    "Game errors/conflicts": {
        "kind": "technical",
        "strong": [
            r"\bcrash(?:es|ed|ing)?\b", r"\blast ?exception\b", r"(?-i:\bLE\b)",
            r"\berror codes?\b", r"\b50/50\b", r"\b50-50\b",
            r"\bconflicts?\b", r"\bconflicting\b", r"\boutdated\b",
            r"\bafter (?:the |a )?(?:latest |new )?patch\b", r"\bupdate broke\b",
            r"\bmods? (?:is |are )?(?:broken|not working|stopped working|don't work|doesn't work)\b",
            r"\bbroke(?:n)? after\b",
        ],
        "weak": [r"\berrors?\b", r"\bbroken\b", r"\bnot working\b", r"\bupdated?\b"],
    },
}
for _t in TAGS.values():
    _t["strong_c"] = [re.compile(p, re.I) for p in _t["strong"]]
    _t["weak_c"] = [re.compile(p, re.I) for p in _t["weak"]]

NEGATION_RE = re.compile(r"\b(?:no|not|never|without|nothing|isn't|wasn't|don't|didn't|doesn't)\s+(?:\w+\s+){0,2}$", re.I)
HEDGE_RE = re.compile(
    r"\?|\bis this\b|\bis it normal\b|\bi think\b|\bmight be\b|\bcould (?:this|it) be\b|\bnot sure\b|\bworried\b|\bscared\b|\bam i\b",
    re.I)

MOD_TYPE_HINTS = {
    "Script mod": [r"\bscript mods?\b", r"\bts4script\b", r"\bmccc\b", r"\bmc command center\b", r"\bwicked ?whims\b", r"\bui cheats\b"],
    "Gameplay mod": [r"\bgameplay mods?\b"],
    "CC: CAS": [r"\bhair(?:s|style|styles)?\b", r"\bclothes\b", r"\bclothing\b", r"\boutfits?\b", r"\bskin ?tones?\b",
                r"\bskinblend\b", r"\bmake-?up\b", r"(?-i:\bCAS\b)"],
    "CC: Build/Buy": [r"\bfurniture\b", r"\bdecor\b", r"\bbuild ?/ ?buy\b", r"\bbuild mode\b", r"\bbuild items?\b"],
}
MOD_TYPE_HINTS_C = {k: [re.compile(p, re.I) for p in v] for k, v in MOD_TYPE_HINTS.items()}

SOURCE_HINTS = {
    "Patreon": [r"patreon"],
    "Tumblr": [r"tumblr"],
    "Discord": [r"discord"],
    "Mod hub": [r"curseforge", r"modthesims", r"mod the sims", r"thesimsresource", r"the sims resource", r"(?-i:\bTSR\b)", r"simsdom", r"nexusmods"],
    "Creator site (possible)": [r"blogspot", r"wixsite", r"carrd\.co", r"neocities", r"github\.io", r"weebly", r"itch\.io"],
    "Other file host": [r"mediafire", r"mega\.nz", r"drive\.google", r"dropbox"],
}
SOURCE_HINTS_C = {k: [re.compile(p, re.I) for p in v] for k, v in SOURCE_HINTS.items()}
URL_RE = re.compile(r"https?://[^\s)\]>]+", re.I)

NEW_COLUMNS = [
    "Suggested tags", "Suggested problem type", "Security certainty (suggested)", "Matched keywords",
    "Review (weak hits)", "Mod/CC type hint", "Source hint", "Link domains",
    "Coder: problem reported", "Coder: problem type", "Coder: mod/CC type", "Coder: download source",
    "Coder: mistake", "Coder: notes",
]


def normalize(text):
    return (text or "").replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def find_hits(text, patterns):
    hits = set()
    for rx in patterns:
        for m in rx.finditer(text):
            if NEGATION_RE.search(text[max(0, m.start() - 30):m.start()]):
                continue
            hits.add(m.group(0).lower())
    return sorted(hits)


def tag_text(text):
    text = normalize(text)
    tags, matched, weak_only = [], {}, {}
    for name, spec in TAGS.items():
        strong = find_hits(text, spec["strong_c"])
        weak = find_hits(text, spec["weak_c"])
        if strong or len(weak) >= 2:
            tags.append(name)
            matched[name] = strong + weak
        elif len(weak) == 1:
            weak_only[name] = weak
    kinds = {TAGS[t]["kind"] for t in tags}
    problem_type = ("both" if kinds == {"security", "technical"} else
                    "security" if kinds == {"security"} else
                    "technical" if kinds == {"technical"} else "none")
    certainty = ""
    if "security" in kinds:
        certainty = "suspected" if HEDGE_RE.search(text) else "check by hand"
    return tags, matched, weak_only, problem_type, certainty


def link_domains(text):
    out = []
    for url in URL_RE.findall(text or ""):
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host and host not in out and "reddit.com" not in host and "redd.it" not in host:
            out.append(host)
    return out


def hint_mod_type(text):
    hits = [n for n, rxs in MOD_TYPE_HINTS_C.items() if any(rx.search(text) for rx in rxs)]
    return "; ".join(hits) if hits else "Other / unclear"


def hint_source(text, domains):
    hay = text + " " + " ".join(domains)
    hits = [n for n, rxs in SOURCE_HINTS_C.items() if any(rx.search(hay) for rx in rxs)]
    return "; ".join(hits) if hits else "Not stated"


def find_col(fieldnames, *names):
    lookup = {(f or "").strip().lower(): f for f in fieldnames}
    for n in names:
        if n in lookup:
            return lookup[n]
    return None


def process(in_path, out_path, fill_tags):
    with open(in_path, newline="", encoding="utf-8-sig") as f:
        lines = f.readlines()
    start = next((i for i, ln in enumerate(lines) if "title" in ln.lower()), 0)
    reader = csv.DictReader(lines[start:])
    fields = list(reader.fieldnames or [])
    rows = list(reader)
    title_col = find_col(fields, "title")
    text_col = find_col(fields, "content", "text", "body")
    link_col = find_col(fields, "post link", "permalink", "link", "url")
    tags_col = find_col(fields, "tags")
    if not (title_col or text_col):
        sys.exit("Couldn't find a 'Title' or 'Content' column. Check the header row of your CSV.")
    out_fields = fields + [c for c in NEW_COLUMNS if c not in fields]
    if tags_col is None:
        tags_col = "Tags"
        if "Tags" not in out_fields:
            out_fields.append("Tags")

    counts = {t: 0 for t in TAGS}
    flagged = 0
    by_source = {}
    out_rows = []
    for row in rows:
        title = row.get(title_col, "") if title_col else ""
        body = row.get(text_col, "") if text_col else ""
        link = row.get(link_col, "") if link_col else ""
        text = normalize(title + "\n" + body)
        tags, matched, weak_only, ptype, certainty = tag_text(text)
        domains = link_domains(normalize(body) + " " + link)
        src = hint_source(text, domains)
        row["Suggested tags"] = "; ".join(tags)
        row["Suggested problem type"] = ptype
        row["Security certainty (suggested)"] = certainty
        row["Matched keywords"] = " | ".join(f"{t}: {', '.join(k)}" for t, k in matched.items())
        row["Review (weak hits)"] = " | ".join(f"{t}: {', '.join(k)}" for t, k in weak_only.items())
        row["Mod/CC type hint"] = hint_mod_type(text)
        row["Source hint"] = src
        row["Link domains"] = "; ".join(domains)
        for c in NEW_COLUMNS:
            row.setdefault(c, "")
        if fill_tags and not (row.get(tags_col) or "").strip():
            row[tags_col] = "; ".join(tags)
        out_rows.append(row)
        for t in tags:
            counts[t] += 1
        if tags:
            flagged += 1
        s = by_source.setdefault(src, [0, 0])
        s[0] += 1
        s[1] += 1 if tags else 0

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    print(f"Saved {out_path}")
    print(f"\nPosts read: {len(out_rows)}   with a suggested problem tag: {flagged}")
    for t, n in counts.items():
        print(f"  {t}: {n}")
    print("\nSuggested problem rate by source hint (rough, before hand coding):")
    for src, (n, k) in sorted(by_source.items(), key=lambda kv: -kv[1][0]):
        print(f"  {src}: {k}/{n} posts ({round(100 * k / n)}%)")
    print("\nThese are keyword suggestions. Read each post and confirm the tags by hand.")


def selftest():
    cases = [
        ("did i get some kind of virus?\nMy game crashed 7-8 times, then my computer crashed. A website transferred me to a crypto website through Edge.",
         {"Malware/virus scare", "Game errors/conflicts", "Scam/fake download page"}),
        ("Windows Defender flagged a trojan in my hair CC download", {"Malware/virus scare"}),
        ("False alarm! There was no virus, just an outdated mod", {"Game errors/conflicts"}),
        ("My save won't load, I think it's corrupted", {"Corrupted/broken save"}),
        ("Can anyone recommend free hair CC from Patreon creators?", set()),
        ("Any update on the new pack?", set()),
        ("Someone DM'd me about a giveaway and asked me to verify my account", {"Phishing/social engineering"}),
        ("My account was hacked after I clicked a download link", {"Account/info theft"}),
    ]
    ok = True
    for text, expected in cases:
        got = set(tag_text(text)[0])
        good = got == expected
        ok &= good
        print(f"[{'ok ' if good else 'FAIL'}] {text.splitlines()[0][:70]}\n       -> {sorted(got)}")
    print("\nSelf-test passed." if ok else "\nSelf-test FAILED.")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description="Suggest keyword tags for a CSV of Sims mod/CC posts.")
    p.add_argument("csv", nargs="?", help="input CSV exported from your spreadsheet")
    p.add_argument("--out", help="output CSV (default: <input>_tagged.csv)")
    p.add_argument("--fill-tags", action="store_true", help="also fill EMPTY Tags cells with the suggested tags")
    p.add_argument("--selftest", action="store_true", help="test the tagging on invented examples and exit")
    a = p.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.csv:
        p.error("give the path to your CSV, or use --selftest")
    out = a.out or re.sub(r"\.csv$", "", a.csv, flags=re.I) + "_tagged.csv"
    process(a.csv, out, a.fill_tags)


if __name__ == "__main__":
    main()