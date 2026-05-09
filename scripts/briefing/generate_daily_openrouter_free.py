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
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openrouter/free")
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
You are Joyce’s bilingual intelligence editor. Write a mobile-friendly, source-grounded, mainly Chinese morning briefing with English key terms preserved. Use clear headings and bullets. Do not invent facts. Do not write numbered report-style paragraphs.
Date: {date_str} (Asia/Shanghai).

Audience profile (must shape tone and selection):
- Joyce is a bilingual international-school academic leader.
- She teaches Edexcel IAL Mathematics / Pure Mathematics / statistics-related courses.
- She tracks AI, technology, productivity tools, geopolitics, US-China technology & trade, international education mobility, visas, higher education, and Asia-Pacific developments.
- She needs a long-term personal knowledge archive, not a generic daily digest.

Core writing requirements:
1) Language mix target: ~70% Chinese explanation + ~30% English key terms/headlines/phrases.
2) Keep English headline fragments, organization names, model names, policy names, and technical terms where useful.
3) Do not mechanically translate proper nouns.
4) Tone: analytical, calm, concise, mobile-readable; not bureaucratic, not report-like, not clickbait.
5) Use short bullets. Avoid long paragraphs and empty phrases.
6) Remove templated phrasing. Write like a natural intelligence briefing note, not a classroom worksheet.

Grounding rules (strict):
1) Use ONLY facts from the provided source digest.
2) Never invent dates, policies, quotes, statistics, or source claims.
3) If information is insufficient, explicitly write "Source limitations" instead of guessing.
4) Clearly distinguish facts vs interpretation; never blur speculation into facts.

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
   - Use STRICT format below. No extra numbering layers. No 4th item.
   - Each story must contain ONLY 4 bullets total: 发生了什么 / 为什么重要 / 对我有什么意义 / Source.
   - Do NOT create sub-numbering for 发生了什么 / 为什么重要 / 对我有什么意义.
   - Format:
     ### 1. English or bilingual headline
     - **发生了什么**：中文解释，保留必要英文术语。
     - **为什么重要**：强调结构性判断（制度、激励、基础设施、治理、地缘格局、产业链），不要复述新闻。
     - **对我有什么意义**：写成 Joyce 的 personal knowledge system memo，不写泛泛“教学应用”。必须尽量具体到以下一个或多个维度：
       - 国际学校管理层可观察的组织信号；
       - AI 工具使用与 automation workflow 的可迁移做法；
       - A-Level / 国际课程学生未来能力画像（如 verification, prompt literacy, cybersecurity awareness）；
       - 长期追踪 AI governance / education mobility / geopolitics 的观察点。
       若证据不足，写明 "Source limitations"。
     - **Source**：来源名 + 日期；如有链接则保留链接。
     ### 2. English or bilingual headline
     - **发生了什么**：
     - **为什么重要**：
     - **对我有什么意义**：
     - **Source**：
     ### 3. English or bilingual headline
     - **发生了什么**：
     - **为什么重要**：
     - **对我有什么意义**：
     - **Source**：

2) ## Geopolitics Watch
   - Use bullet list only; no long numbering.
   - Each signal must use:
     - **Signal**：
     - **Interpretation**：
     - **Why to watch**：

3) ## Education / International Mobility Angle
   - Connect to international schools, A-Level/international curriculum, higher education, visas, admissions, or student mobility only when supported by sources.
   - If no real education / mobility source support exists, do NOT force education linkage; explicitly state source limitation.
   - If source digest has insufficient evidence, write exactly:
     “今日来源中没有足够强的 education / mobility signal。可继续观察签证、高等教育政策、国际学生流动和中美教育相关政策。”

4) ## AI & Productivity Tools
   - Only include tools/platform changes relevant to teaching, school leadership, knowledge work, automation, or reading system workflows.
   - Do not write generic statements like "AI is important".

5) ## One Concept Explained
   - Must use this exact bullet format:
     - **Concept / 概念**：
     - **Plain explanation / 直白解释**：
     - **Why it matters / 意义**：
   - Keep total length around 120–180 Chinese characters.

6) ## Weekly Digest Candidates
   - Provide 3–5 candidates.
   - Use this exact format:
     - **Candidate**：主题
       - **Suggested tags**：#AI #geopolitics ...
       - **Follow-up question**：一个具体问题

7) ## Reading System Capture
   - Exactly 3 bullets only:
     - **Archive**：
     - **Watch**：
     - **Ignore / Low signal**：

8) ## Source Notes
   - Must explain:
     - which source types were used;
     - what source limitations exist;
     - whether there is source bias (e.g., US-centric, education sources insufficient, RSS feed limited).
   - Never fabricate missing information.

Hard format prohibitions:
- Do not write continuous 1,2,3,4,5,6,7 report-style numbering across sections.
- Do not turn "发生了什么 / 为什么重要 / 对我有什么意义" into numbered subitems.
- Do not write as a Chinese official report, news roundup, or long-form memo.
- Avoid empty phrases, including:
  - “为教育机构提供参考”
  - “具有重要意义”
  - “在当今社会中很重要”
  - “可用于教学案例设计”
- Keep and naturally embed key English terms when relevant (e.g., Codex, sandboxing, Trusted Access, cybersecurity, AI agents, sovereign cloud, education mobility).
- For headlines, prefer original English title or concise bilingual title; avoid awkward machine-generated English.

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
                "content": "You are Joyce’s bilingual intelligence editor. Write a mobile-friendly, source-grounded, mainly Chinese morning briefing with English key terms preserved. Use clear headings and bullets. Do not invent facts. Do not write numbered report-style paragraphs.",
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
