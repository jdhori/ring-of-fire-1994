#!/usr/bin/env python3
"""
render_diagrams.py — render the Mermaid sources in charts/ to static, PDF-safe SVGs.

Mermaid diagrams (e.g. the Figure 1-1 family tree) are embedded in the HTML/PDF editions
the same layered way as the charts: one accessible <figure> carrying the rendered SVG plus a
real data table (see embed.build_mermaid_html / the <!--MERMAID id--> token in build_html.py).
This step produces that SVG.

Two things make the output usable in the *tagged PDF* (WeasyPrint runs no JS and cannot draw
SVG <foreignObject>):
  * mermaid.config.json sets htmlLabels:false, so node/edge labels become native <text>/<tspan>
    nodes (not <foreignObject> HTML) — otherwise the PDF would show empty boxes;
  * the .mmd carries accTitle/accDescr, which Mermaid emits as <title>/<desc> for screen readers.

mermaid-cli (mmdc) needs a Chromium to lay out the SVG. We point it at puppeteer's
chrome-headless-shell if present, else a system Chrome/Chromium. If none is found we leave the
already-committed SVG in place and skip (so `make html`/`make pdf` still succeed offline).

Usage:  python3 charts/render_diagrams.py
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "mermaid.config.json")
PUPPETEER = os.path.join(HERE, "puppeteer.config.json")
STATIC = os.path.join(HERE, "static")

# mmd source (relative to charts/) -> output SVG name in charts/static/
DIAGRAMS = {"family-tree.mmd": "family-tree.svg"}


def find_chrome():
    """Return a Chromium executable path for mmdc, or None to skip rendering."""
    env = os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if env and os.path.exists(env):
        return env
    cache = os.path.join(os.path.expanduser("~"), ".cache", "puppeteer")
    hits = sorted(glob.glob(os.path.join(
        cache, "chrome-headless-shell", "*", "chrome-headless-shell-linux64",
        "chrome-headless-shell")))
    if hits:
        return hits[-1]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


def main():
    mmdc = shutil.which("mmdc")
    chrome = find_chrome()
    if not mmdc or not chrome:
        missing = "mmdc (npm i -g @mermaid-js/mermaid-cli)" if not mmdc else "a Chromium for mmdc"
        print(f"render_diagrams: skipping — {missing} not found; keeping committed SVGs.",
              file=sys.stderr)
        return 0

    os.makedirs(STATIC, exist_ok=True)
    env = dict(os.environ, PUPPETEER_EXECUTABLE_PATH=chrome)
    for src, out in DIAGRAMS.items():
        in_path = os.path.join(HERE, src)
        out_path = os.path.join(STATIC, out)
        subprocess.run(
            [mmdc, "-i", in_path, "-o", out_path, "-c", CONFIG,
             "-p", PUPPETEER, "-b", "transparent"],
            check=True, env=env)
        print(f"render_diagrams: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
