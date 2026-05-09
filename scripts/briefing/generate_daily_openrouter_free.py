from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import feedparser
import yaml
from dateutil import parser as date_parser
from openai import OpenAI

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
MODEL_NAME = "openrouter/free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
HTTP_REFERER = "https://joyce23523.github.io/reading-assistant/"
X_OPENROUTER_TITLE = "Joyce Reading Assistant"

SOURCES_FILE = Path("scripts/briefing/sources.yml")
OUTPUT_DIR = Path("docs/briefings/daily")
MAX_ITEMS_PER_SOURCE = 4
MAX_TOTAL_ITEMS = 40
MAX_SUMMARY_LENGTH = 240


def today_shanghai_str() -> str:
    return datetime.now(SHANGHAI_TZ).date().isoformat()


def force_enabled() -> bool:
    return os.getenv("FORCE", "false").strip().lower() == "true"


def parse_published(entry: Any) -> str:
    raw = (
        entry.get("published")
        or entry.get("updated")
        or entry.get("pubDate")
        or ""
    )
    if not raw:
        return "unknown"
    try:
        dt = date_parser.parse(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=SHANGHAI_TZ)
        return dt.astimezone(SHANGHAI_TZ).strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return raw[:40]


def compact_text(text: str, limit: int = MAX_SUMMARY_LENGTH) -> str:
    normalized = " ".join((text or "").split())
    return normalized[:limit]


def load_sources() -> list[dict[str, str]]:
    if not SOURCES_FILE.exists():
        raise FileNotFoundError(f"sources file not found: {SOURCES_FILE}")

    data = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}
    sources = data.get("sources", [])
    valid_sources: list[dict[str, str]] = []
    for source in sources:
        name = (source or {}).get("name")
        rss = (source or {}).get("rss")
        if name and rss:
            valid_sources.append({"name": str(name), "rss": str(rss)})
    return valid_sources


def collect_source_digest(sources: list[dict[str, str]]) -> tuple[str, list[str], int]:
    warnings: list[str] = []
    blocks: list[str] = []
    total_items = 0

    for source in sources:
        if total_items >= MAX_TOTAL_ITEMS:
            break

        name = source["name"]
        rss = source["rss"]
        parsed = feedparser.parse(rss)
        if parsed.bozo:
            warnings.append(f"warning: failed to parse source '{name}'")
            continue

        entries = parsed.entries[:MAX_ITEMS_PER_SOURCE]
        if not entries:
            warnings.append(f"warning: no entries for source '{name}'")
            continue

        lines = [f"Source: {name}"]
        source_count = 0
        for entry in entries:
            if total_items >= MAX_TOTAL_ITEMS:
                break
            title = compact_text(entry.get("title", "(no title)"), 180)
            summary = compact_text(entry.get("summary", ""), MAX_SUMMARY_LENGTH)
            link = entry.get("link", "")
            published = parse_published(entry)
            lines.append(
                f"- title: {title}\n"
                f"  published: {published}\n"
                f"  summary: {summary}\n"
                f"  link: {link}"
            )
            source_count += 1
            total_items += 1

        if source_count > 0:
            blocks.append("\n".join(lines))

    digest = "\n\n".join(blocks)
    return digest, warnings, total_items


def build_prompt(date_str: str, source_digest: str) -> str:
    return f"""
You are generating a bilingual (Chinese-English) Morning Intelligence Briefing.
Date: {date_str} (Asia/Shanghai).

STRICT RULES:
1) Use ONLY facts from the provided source digest.
2) If information is insufficient, explicitly say Source limitations and do NOT fabricate facts.
3) Keep multi-source perspectives when possible.
4) Separate confirmed facts, interpretation, and implications.

Coverage priorities:
- technology, AI, education technology, productivity tools, technology regulation
- geopolitics (especially US-China technology/trade, global security, major elections)
- international education mobility, visas, higher education, Asia-Pacific developments

Output format must be Markdown and must include EXACTLY these sections and headings:
#MIB_{date_str}

# Morning Intelligence Briefing｜{date_str}

## Top 3 Tech & AI Stories
## Geopolitics Watch
## Education / International Mobility Angle
## AI & Productivity Tools
## One Concept Explained
## Weekly Digest Candidates
## Reading System Capture
## Source Notes

Requirements for sections:
- Top 3 Tech & AI Stories: list 3 items with brief CN/EN descriptions.
- Weekly Digest Candidates: provide 3–5 candidate bullets.
- Reading System Capture: state whether to archive into weekly review and why.
- Source Notes: include "Source limitations" when needed.

Here is the source digest:
{source_digest}
""".strip()


def generate_briefing(date_str: str, source_digest: str, api_key: str) -> str:
    client = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": HTTP_REFERER,
            "X-OpenRouter-Title": X_OPENROUTER_TITLE,
        },
    )

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Return concise, factual Markdown only."},
            {"role": "user", "content": build_prompt(date_str, source_digest)},
        ],
        temperature=0.3,
    )

    content = (completion.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("OpenRouter returned empty content")
    return content


def main() -> None:
    date_str = today_shanghai_str()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{date_str}.md"

    if output_file.exists() and not force_enabled():
        print(f"already exists: {output_file}")
        return

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("error: OPENROUTER_API_KEY is required", file=sys.stderr)
        raise SystemExit(1)

    sources = load_sources()
    digest, warnings, total_items = collect_source_digest(sources)

    if not digest:
        print("error: no source items available from RSS sources", file=sys.stderr)
        raise SystemExit(1)

    try:
        markdown = generate_briefing(date_str, digest, api_key)
    except Exception as exc:
        print(f"error: OpenRouter API call failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    output_file.write_text(markdown + "\n", encoding="utf-8")
    print(f"generated: {output_file} (items={total_items})")

    for warning in warnings:
        print(warning)


if __name__ == "__main__":
    main()
