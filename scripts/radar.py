#!/usr/bin/env python3
"""Daily arXiv radar for awesome-self-improving-coding-agents.

Fetches today's arXiv announcement feeds (rss.arxiv.org) for selected cs.*
categories, keeps entries whose title/abstract match self-improvement keyword
groups, and rewrites ``docs/radar.md`` with a rolling archive (entries expire
after ``RETENTION_DAYS``). Stdlib only.

Notes:
- rss.arxiv.org lists only the current day's announcements (none on US
  weekends/holidays); the rolling archive in docs/radar.md carries entries
  across days, so a quiet day simply re-writes the existing set.

Usage:
    python scripts/radar.py              # fetch live, rewrite docs/radar.md
    python scripts/radar.py --selftest   # parse+render an embedded fixture, no network
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RSS = "https://rss.arxiv.org/rss"
CATEGORIES = ["cs.SE", "cs.CL", "cs.AI", "cs.LG"]
RETENTION_DAYS = 21
REPO = "vicfei/awesome-self-improving-coding-agents"

# Keyword groups, applied to title + abstract (case-insensitive).
STRONG = re.compile(
    r"self-improv|self-evolv|recursive self-improvement|self-referential|self-modif|\bAI4AI\b",
    re.IGNORECASE,
)
CODING = re.compile(
    r"coding agent|code agent|software engineer|\bSWE\b|program synthesis|code generation|"
    r"automated programm|developer|autonomous cod",
    re.IGNORECASE,
)
ARXIV_ID_IN_TITLE = re.compile(r"\(arXiv:([0-9]{4}\.[0-9]{4,6})(v\d+)?\)\s*$")

RSS_ITEM_FIXTURE = """<?xml version='1.0' encoding='UTF-8'?>
<rss xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
  <channel>
    <title>cs.SE updates on arXiv.org</title>
    <item>
      <title>A Self-Improving Coding Agent That Ships (arXiv:2609.00001v1)</title>
      <link>http://arxiv.org/abs/2609.00001v1</link>
      <description>An agent that rewrites its own harness for software engineering.</description>
      <pubDate>Mon, 28 Sep 2026 00:30:44 GMT</pubDate>
    </item>
    <item>
      <title>Boring static analysis paper (arXiv:2609.00002v1)</title>
      <link>http://arxiv.org/abs/2609.00002v1</link>
      <description>Not about self-improvement at all.</description>
      <pubDate>Mon, 28 Sep 2026 00:30:44 GMT</pubDate>
    </item>
    <item>
      <title>Self-Evolving World Models | pipe test (arXiv:2609.00003v1)</title>
      <link>http://arxiv.org/abs/2609.00003v1</link>
      <description>World models that improve themselves through play.</description>
      <pubDate>Mon, 28 Sep 2026 00:30:44 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def http_get(url: str, attempts: int = 3, timeout: int = 30) -> bytes:
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (radar fetcher)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as err:  # noqa: BLE001 - retry any transport error
            last_err = err
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"GET failed after {attempts} attempts: {url} ({last_err})")


def parse_rss(xml: bytes, category: str) -> list[dict[str, str]]:
    """Return today's self-improvement matches from one category feed."""
    out: list[dict[str, str]] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return out
    for item in root.iter("item"):
        raw_title = " ".join((item.findtext("title") or "").split())
        desc = " ".join((item.findtext("description") or "").split())
        m = ARXIV_ID_IN_TITLE.search(raw_title)
        if not m:
            continue
        arxiv_id, title = m.group(1), ARXIV_ID_IN_TITLE.sub("", raw_title).strip()
        # STRONG matches on title only: abstracts routinely *mention* self-improvement
        # ("we do not focus on self-improvement") and would flood the radar.
        if not STRONG.search(title):
            continue
        tag = "coding+" if CODING.search(f"{title} {desc}") else "self-improvement"
        out.append({"id": arxiv_id, "title": title, "category": category, "tag": tag})
    return out


def fetch_today() -> list[dict[str, str]]:
    seen: dict[str, dict[str, str]] = {}
    for cat in CATEGORIES:
        for e in parse_rss(http_get(f"{RSS}/{cat}"), cat):
            seen.setdefault(e["id"], e)
    return sorted(seen.values(), key=lambda e: e["id"], reverse=True)


ROW = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\[(.+?)\]\(https://arxiv\.org/abs/([^)]+)\)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|$")


def load_existing(rad: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    if not rad.exists():
        return entries
    for line in rad.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line.strip())
        if m:
            entries.append(
                {"first_seen": m.group(1), "title": m.group(2), "id": m.group(3), "category": m.group(4), "tag": m.group(5)}
            )
    return entries


def merge(old: list[dict[str, str]], fresh: list[dict[str, str]], today: str) -> list[dict[str, str]]:
    by_id = {e["id"]: e for e in old}
    for e in fresh:
        if e["id"] not in by_id:
            by_id[e["id"]] = {"first_seen": today, **e}
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=RETENTION_DAYS)).isoformat()
    return [e for e in by_id.values() if e["first_seen"] >= cutoff]


def render(entries: list[dict[str, str]], now: dt.datetime) -> str:
    entries = sorted(entries, key=lambda e: (e["first_seen"], e["id"]), reverse=True)
    lines = [
        f"<!-- Auto-generated by scripts/radar.py via GitHub Actions (repo: {REPO}). Manual edits will be overwritten. -->",
        "# 🤖 arXiv Radar",
        "",
        "Papers matching this repo's [keyword filter](../scripts/radar.py), collected from the daily "
        "arXiv announcement RSS feeds (cs.SE / cs.CL / cs.AI / cs.LG) and kept for a "
        f"{RETENTION_DAYS}-day rolling window. Refreshed daily — generated {now.strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
    ]
    if not entries:
        lines += [
            "_No matches in the current window — either a quiet stretch or the weekend "
            "(arXiv announces on US weekdays). Tune keywords via a PR if this stays empty._",
            "",
        ]
    else:
        n = len(entries)
        lines += [f"**{n} paper{'s' if n != 1 else ''}** on radar.", "", "| First seen | Paper | Area | Match |", "|---|---|---|---|"]
        for e in entries:
            title = e["title"].replace("|", "\\|")
            lines.append(
                f"| {e['first_seen']} | [{title}](https://arxiv.org/abs/{e['id']}) | {e['category']} | {e['tag']} |"
            )
    lines += [
        "",
        "---",
        "",
        "Hand-curated sections live in the [main README](../README.md). Keywords are defined at the top "
        "of [`scripts/radar.py`](../scripts/radar.py) — PRs welcome.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    rad = Path(__file__).resolve().parent.parent / "docs" / "radar.md"
    merged = merge(load_existing(rad), fetch_today(), now.strftime("%Y-%m-%d"))
    rad.write_text(render(merged, now), encoding="utf-8")
    print(f"radar: archive holds {len(merged)} entries -> {rad}")
    return 0


def selftest() -> int:
    items = parse_rss(RSS_ITEM_FIXTURE.encode(), "cs.SE")
    assert len(items) == 2, f"expected strong-filter to keep 2 of 3, got {len(items)}: {items}"
    assert items[0]["id"] == "2609.00001" and items[0]["tag"] == "coding+", items
    assert items[1]["id"] == "2609.00003" and items[1]["tag"] == "self-improvement", items
    now = dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc)
    merged = merge([], items, "2026-09-28")
    assert len(merged) == 2 and merged[0]["first_seen"] == "2026-09-28"
    md = render(merged, now)
    assert "pipe test" in md and "\\\\|" not in md and "\\|" in md, "pipe escaping wrong"
    # round-trip: rendered markdown parses back into the archive format
    rt_path = Path("/tmp/_radar_rt.md")
    rt_path.write_text(md, encoding="utf-8")
    rt = load_existing(rt_path)
    assert len(rt) == 2 and rt[0]["id"] in {"2609.00001", "2609.00003"}, f"round-trip lost rows: {rt}"
    print("selftest OK — RSS parse, strong/coding tags, merge, render, archive round-trip:")
    print(md[:600])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="run offline fixture test")
    args = ap.parse_args()
    sys.exit(selftest() if args.selftest else main())
