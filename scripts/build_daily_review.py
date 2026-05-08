#!/usr/bin/env python3
"""Build a structured Markdown review from a daily audiobook log.

Usage:
    python3 scripts/build_daily_review.py notes/2026-05-08-log.md
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

TARGET_SECTIONS = [
    "Date",
    "Book Info",
    "Summary (EN)",
    "摘要（中文）",
    "Key Quotes",
    "Vocabulary (Raw)",
    "Reflection",
]


def parse_sections(md_text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = None

    for line in md_text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    return sections


def render_review(source_path: Path, sections: Dict[str, List[str]]) -> str:
    lines: List[str] = []
    lines.append("# Daily Review (Structured)")
    lines.append("")
    lines.append(f"- Source File: `{source_path.name}`")
    lines.append("")

    for name in TARGET_SECTIONS:
        lines.append(f"## {name}")
        content = sections.get(name, [])
        if content and any(c.strip() for c in content):
            lines.extend(content)
        else:
            lines.append("- (empty)")
        lines.append("")

    lines.append("## Next Step Suggestion")
    lines.append("- Re-listen one difficult segment and write 3 EN sentences + 3 中文总结。")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a structured Markdown review from a daily log file."
    )
    parser.add_argument("input_file", type=Path, help="Path to a Markdown daily log file")
    args = parser.parse_args()

    input_path = args.input_file
    if not input_path.exists() or not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    text = input_path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    output_text = render_review(input_path, sections)

    output_path = input_path.with_suffix(input_path.suffix + ".review.md")
    output_path.write_text(output_text, encoding="utf-8")

    print(f"Review generated: {output_path}")


if __name__ == "__main__":
    main()
