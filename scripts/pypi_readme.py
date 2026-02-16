#!/usr/bin/env python3
"""Rewrite relative links in README.md to absolute GitHub URLs for PyPI.

PyPI renders README.md but cannot resolve relative links to repo files.
This script rewrites them to absolute URLs so PDFs and docs are clickable
on the PyPI project page.

Usage:
    python scripts/pypi_readme.py          # rewrite README.md in place
    python scripts/pypi_readme.py --check  # dry-run, print what would change

After building (python -m build), restore the original:
    git checkout README.md
"""

import re
import sys
from pathlib import Path

REPO = "kormco/deepagents-printshop"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
BLOB_BASE = f"https://github.com/{REPO}/blob/{BRANCH}"

# Binary files get raw URLs (direct download)
RAW_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg"}

README = Path(__file__).parent.parent / "README.md"


def rewrite_links(content: str) -> str:
    """Rewrite relative markdown links to absolute GitHub URLs."""

    def replace_link(match: re.Match) -> str:
        text = match.group(1)
        url = match.group(2)

        # Skip already-absolute URLs
        if url.startswith(("http://", "https://", "#")):
            return match.group(0)

        # Strip leading ./ if present
        clean = url.lstrip("./")
        ext = Path(clean).suffix.lower()

        if ext in RAW_EXTENSIONS:
            return f"[{text}]({RAW_BASE}/{clean})"
        else:
            return f"[{text}]({BLOB_BASE}/{clean})"

    # Match markdown links: [text](url)
    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", replace_link, content)


def main():
    check_only = "--check" in sys.argv

    content = README.read_text(encoding="utf-8")
    rewritten = rewrite_links(content)

    if content == rewritten:
        print("No relative links found — README already uses absolute URLs.")
        return

    if check_only:
        # Show a diff-like summary
        original_lines = content.splitlines()
        rewritten_lines = rewritten.splitlines()
        changes = 0
        for i, (old, new) in enumerate(zip(original_lines, rewritten_lines), 1):
            if old != new:
                changes += 1
                print(f"L{i}:")
                print(f"  - {old.strip()}")
                print(f"  + {new.strip()}")
        print(f"\n{changes} line(s) would change. Run without --check to apply.")
    else:
        README.write_text(rewritten, encoding="utf-8")
        print(f"Rewrote relative links in {README}")
        print("Remember to restore after building: git checkout README.md")


if __name__ == "__main__":
    main()
