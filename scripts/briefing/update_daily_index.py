from __future__ import annotations

import re
from pathlib import Path


DAILY_DIR = Path("docs/briefings/daily")
INDEX_FILE = Path("docs/briefings/daily.md")
DATE_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


def collect_daily_files() -> list[str]:
    dates: list[str] = []
    if not DAILY_DIR.exists():
        return dates

    for file in DAILY_DIR.glob("*.md"):
        match = DATE_FILE_RE.match(file.name)
        if match:
            dates.append(match.group(1))

    return sorted(dates, reverse=True)


def to_link_line(date_str: str) -> str:
    return f"- [{date_str}](daily/{date_str}.md)"


def build_index_content(dates: list[str]) -> str:
    recent = dates[:7]
    archive = dates[7:]

    lines: list[str] = [
        "# Daily Briefings",
        "",
        "Daily briefings are generated automatically and later consolidated into weekly reviews.",
        "",
        "## Recent Daily Briefings",
        "",
    ]

    if recent:
        lines.extend(to_link_line(d) for d in recent)
    else:
        lines.append("- No briefings yet.")

    lines.extend(["", "## Archive", ""])

    if archive:
        lines.extend(to_link_line(d) for d in archive)
    else:
        lines.append("- No archived briefings yet.")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    dates = collect_daily_files()
    content = build_index_content(dates)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(content, encoding="utf-8")
    print(f"updated: {INDEX_FILE}")


if __name__ == "__main__":
    main()
