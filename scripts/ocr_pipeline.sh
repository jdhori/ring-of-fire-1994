#!/usr/bin/env bash
# ocr_pipeline.sh — regenerate page renders + OCR text from the source PDF.
# Only needed if you are re-deriving figures/text from scratch; the committed
# build/ section files and document/images already contain the finished work.
#
# Requires: poppler-utils (pdftoppm), tesseract-ocr
# Usage:    bash scripts/ocr_pipeline.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PDF="$ROOT/source/RingofFire1994.pdf"
PAGES="$ROOT/work/pages"; OCR="$ROOT/work/ocr"
mkdir -p "$PAGES" "$OCR"
echo "Rendering pages at 200 DPI..."
pdftoppm -r 200 -jpeg "$PDF" "$PAGES/p"
echo "Running OCR (tesseract --psm 1)..."
for img in "$PAGES"/p-*.jpg; do
  base="$(basename "$img" .jpg)"
  tesseract "$img" "$OCR/$base" --psm 1 >/dev/null 2>&1 || true
done
echo "Done. Pages in $PAGES, OCR text in $OCR."
echo "NOTE: tables/figures OCR poorly — transcribe those by viewing the page images."
