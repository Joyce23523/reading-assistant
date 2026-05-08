#!/usr/bin/env python3
"""Create weekly or monthly digest files from templates."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
BRIEFINGS_DIR = ROOT / "briefings"

WEEKLY_PATTERN = re.compile(r"^\d{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$")
MONTHLY_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def usage() -> str:
    return (
        "Usage:\n"
        "  python scripts/create_digest_file.py weekly YYYY-Www\n"
        "  python scripts/create_digest_file.py monthly YYYY-MM"
    )


def create_digest(kind: str, period: str) -> Path:
    if kind == "weekly":
        if not WEEKLY_PATTERN.match(period):
            raise ValueError("Invalid weekly period, expected format like 2026-W19")
        template_path = TEMPLATE_DIR / "weekly_digest_template.md"
        output_path = BRIEFINGS_DIR / "weekly" / f"{period}.md"
        placeholder = "{{WEEK}}"
    elif kind == "monthly":
        if not MONTHLY_PATTERN.match(period):
            raise ValueError("Invalid monthly period, expected format like 2026-05")
        template_path = TEMPLATE_DIR / "monthly_digest_template.md"
        output_path = BRIEFINGS_DIR / "monthly" / f"{period}.md"
        placeholder = "{{MONTH}}"
    else:
        raise ValueError("Kind must be either 'weekly' or 'monthly'")

    content = template_path.read_text(encoding="utf-8")
    content = content.replace(placeholder, period)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"File already exists: {output_path}")
    output_path.write_text(content, encoding="utf-8")

    return output_path


def main() -> int:
    if len(sys.argv) != 3:
        print(usage())
        return 1

    kind = sys.argv[1].strip().lower()
    period = sys.argv[2].strip()

    try:
        created = create_digest(kind, period)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        print(f"Error: {exc}")
        print()
        print(usage())
        return 1

    print(f"Created: {created.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
