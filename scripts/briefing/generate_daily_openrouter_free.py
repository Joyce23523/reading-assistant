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
You are Joyce's bilingual intelligence editor.
Date: {date_str} (Asia/Shanghai).

Audience profile (must shape tone and selection):
- Joyce is a bilingual international-school academic leader.
- She teaches Edexcel IAL Mathematics / Pure Mathematics / statistics-related courses.
- She tracks AI, technology, productivity tools, geopolitics, US-China technology & trade, international education mobility, visas, higher education, and Asia-Pacific developments.
- She needs a long-term personal knowledge archive, not a generic daily digest.

Core writing requirements:
1) Output must be mainly Chinese, with natural bilingual support (Chinese explanation + English key terms).
2) Preserve English names, source titles, organisations, technical terms, and useful original expressions.
3) Avoid long English-only paragraphs and avoid mechanical full translation of proper nouns.
4) Tone: analytical, calm, concise but not shallow; slightly sharp when appropriate; non-corporate; non-clickbait; non-generic.
5) Avoid empty phrases (for example, "this is important in today's world").

Grounding rules (strict):
1) Use ONLY facts from the provided source digest.
2) Never invent dates, policies, quotes, statistics, or source claims.
3) If information is insufficient, explicitly write "Source limitations" instead of guessing.
4) Clearly separate: 已确认事实 (Confirmed facts) / 解读 (Interpretation) / 可能影响 (Implications).

Coverage priorities:
- technology, AI, education technology, productivity tools, technology regulation
- geopolitics structural signals (especially US-China technology/trade, global security, Asia-Pacific, policy shifts)
- international education mobility, visas, higher education, admissions, international curriculum implications

Boundary:
- Do NOT include routine health / neuroscience / family health content in this Morning Intelligence Briefing.
- Only include health-related content if it is a major global public event supported by the source digest.

Output must be Markdown and must include EXACTLY these sections and headings:
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

Section instructions (follow exactly):
1) ## Top 3 Tech & AI Stories
   - Choose only the 3 most useful AI/technology items.
   - For each item, include:
     - 发生了什么 / What happened
     - 为什么重要 / Why it matters
     - 对我有什么意义 / Why it matters to me
   - Each item must explicitly label: 已确认事实 / 解读 / 可能影响.

2) ## Geopolitics Watch
   - Focus on structural signals, not every dramatic headline.
   - Prioritise US-China technology/trade, global security, Asia-Pacific, policy shifts, and mobility implications.
   - Explicitly label: 已确认事实 / 解读 / 可能影响.

3) ## Education / International Mobility Angle
   - Connect relevant items to international schools, A-Level / international curriculum, higher education, visas, admissions, or student mobility only when supported by sources.
   - If support is weak or absent, say "Source limitations" clearly.
   - Explicitly label: 已确认事实 / 解读 / 可能影响.

4) ## AI & Productivity Tools
   - Focus on tools/workflows for knowledge work, teaching, school leadership, research, reading, or automation.
   - Avoid generic "tool news" without practical angle.

5) ## One Concept Explained
   - Explain one concept in a bilingual-friendly way (Chinese-led, English key terms kept).
   - Keep it practical and concise; avoid textbook-style overexpansion.

6) ## Weekly Digest Candidates
   - Provide 3–5 candidates for Sunday weekly review.
   - For each candidate include: brief reason, suggested tags, and one follow-up question.

7) ## Reading System Capture
   - State what should be archived now, ignored now, and watched.
   - Help maintain a long-term reading-assistant knowledge archive.

8) ## Source Notes
   - Mention source limitations, including if coverage is narrow, US-centric, outdated, or weak for education mobility.
   - Never fabricate missing information.

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
            {
                "role": "system",
                "content": (
                    "You are Joyce's bilingual intelligence editor. "
                    "Produce source-grounded, mainly Chinese, analytical Markdown. "
                    "Do not invent facts."
                ),
            },
            {"role": "user", "content": build_prompt(date_str, source_digest)},
        ],
        temperature=0.25,
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
