#!/usr/bin/env python3
"""
assemble.py — concatenate the per-section Markdown in build/ into the full report.

The canonical text lives as ordered section files in build/ (00-front.md ... 14-addendum.md).
Edit those, then run this to regenerate document/Ring-of-Fire-1994.md, then run build_html.py.

Usage:  python scripts/assemble.py
"""
import glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "document", "Ring-of-Fire-1994.md")

def main():
    files = sorted(glob.glob(os.path.join(BUILD, "*.md")))
    if not files:
        raise SystemExit(f"No section files found in {BUILD}")
    parts = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            parts.append(fh.read())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))
    print(f"Assembled {len(files)} sections -> {OUT}")
    for f in files:
        print("  +", os.path.basename(f))

if __name__ == "__main__":
    main()
