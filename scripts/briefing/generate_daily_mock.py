from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
OUTPUT_DIR = Path("docs/briefings/daily")


def today_shanghai_str() -> str:
    return datetime.now(SHANGHAI_TZ).date().isoformat()


def build_mock_content(date_str: str) -> str:
    placeholder = "This is a mock briefing generated for pipeline testing."
    return f"""#MIB_{date_str}

# Morning Intelligence Briefing｜{date_str}

## Top 3 Tech & AI Stories
{placeholder}

## Geopolitics Watch
{placeholder}

## Education / International Mobility Angle
{placeholder}

## AI & Productivity Tools
{placeholder}

## One Concept Explained
{placeholder}

## Weekly Digest Candidates
{placeholder}

## Reading System Capture
{placeholder}
"""


def main() -> None:
    date_str = today_shanghai_str()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{date_str}.md"

    if output_file.exists():
        print(f"already exists: {output_file}")
        return

    output_file.write_text(build_mock_content(date_str), encoding="utf-8")
    print(f"generated: {output_file}")


if __name__ == "__main__":
    main()
