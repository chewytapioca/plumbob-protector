# Plumbob Protector ✧(≧◡≦)

A safe-modding guide for Sims 4 players and creators, built from what players actually report on Reddit. We read posts about custom content (CC) and mods, code what went right or wrong, and turn the patterns into a source risk score and an interactive guide.

Course project for INFO 410. Team: Stephanie Lee and Christina Nguyen.

## What we are trying to learn

- What problems do players report when they download CC and mods?
- Where do those downloads come from, and do some sources come up with problems more often than others?
- What should a player check before and after downloading to stay safe?

## How it works

1. **Collect.** We hand-pick Reddit posts (r/thesims, r/ModTheSims4, r/sims4cc, r/thesimscc, r/Sims4) and copy each into a spreadsheet. Target: 300+ posts.
2. **Code.** Each post gets an Issue Type tag and a `Sources:` note listing any download sources it names.
3. **Analyze.** Scripts suggest tags, count common words, and chart which sources appear with problems.
4. **Publish.** Findings feed a source risk score and the guide page.

## The spreadsheet

Seven columns, in this order:

| Column | What goes in it |
|---|---|
| Date | Post date (approximate when Reddit only shows "3y ago") |
| Subreddit | e.g. `r/thesims` |
| Issue Type | One or more tags from the list below |
| Post Link | URL of the post |
| Title | Post title |
| Content | Post text, with images marked `[Image]` |
| Additional Notes | Only `Sources: ...`, or `Sources: Not stated` |

No usernames are stored.

## Issue Type tags

| Tag | Meaning |
|---|---|
| Malware/virus scare | Virus, malware, trojan, or antivirus warnings |
| Account/info theft | Hacked accounts, stolen passwords or data |
| Scam/fake download page | Pop-ups, redirects, fake download buttons, shady sites |
| Phishing/social engineering | Fake messages, giveaways, requests for logins |
| Corrupted/broken save | Lost or damaged saves |
| Game errors/conflicts | Crashes and mod conflicts, with no security issue |
| Download help/how to | Asking where to find, install, or make mods and CC |
| No problem | No issue reported |

## Files

| File | What it does |
|---|---|
| `main.py` | Keyword tagger. Reads the CSV and suggests tags for each post. Writes `<name>_tagged.csv`. |
| `bubbles.py` | Makes bubble pictures (SVG) of common words, tag counts, or sources, colored by problem rate. |

Both scripts use only Python's standard library. There is nothing to install.

## Quick start

Put your CSV export in the same folder as the scripts, then run these from the project folder. The scripts skip any junk line above the header row.

```
python main.py "INFO410 Coding - Data Collection.csv"
python main.py --selftest

python bubbles.py "INFO410 Coding - Data Collection.csv"
python bubbles.py "INFO410 Coding - Data Collection.csv" --tags
python bubbles.py "INFO410 Coding - Data Collection.csv" --sources
python bubbles.py "INFO410 Coding - Data Collection.csv" --problems-only
python bubbles.py "INFO410 Coding - Data Collection.csv" --tag "Malware/virus scare"
```

On Windows, if `python` is not recognized, use the full path to `python.exe` (the Microsoft Store version lives in `%LOCALAPPDATA%\Microsoft\WindowsApps`) or try `py`.

Open the `.svg` files in any browser.

## How the tagger works

Rule-based text processing, not machine learning. It normalizes text, matches strong and weak keyword patterns for each tag, skips negated phrases like "no virus", and marks hedged wording ("is this a virus?") as suspected. Strong keywords tag a post alone, and weak keywords need two different hits. Its output is a suggestion. A person reads each post and confirms the tag.

## Status

- 154 posts coded so far, toward 300+.
- `Sources:` notes are still missing on most problem posts, so source problem rates are not reliable yet.
- Phishing/social engineering has very few posts.

## Limitations

- Reddit posts are written by people who chose to post, so counts show what gets reported, not how often problems really happen.
- Sources with only a few posts should not get a risk label.
- Early sampling leaned toward r/sims4cc.

## Next steps

- Fill in `Sources:` for every problem post and reach 300+ posts.
- Compute a source risk score with a minimum sample size and a confidence interval.
- Measure how well the tagger agrees with hand coding.
- Build the interactive guide page from the findings.

## Data and ethics

We collect posts by hand for a class project. We keep no usernames, and the dataset is not redistributed. We do not train machine learning models on Reddit content. Please follow Reddit's terms if you reuse any of this.

## Disclaimer

Plumbob Protector is a student project. It is not affiliated with EA or Maxis, and its guidance does not guarantee safety.