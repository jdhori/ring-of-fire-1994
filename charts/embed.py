#!/usr/bin/env python3
"""
embed.py — build an embeddable, accessible chart fragment for the HTML/PDF edition.

For each chart in charts.json this produces one <figure> that carries the same data three
ways (the project's layered pattern), tuned so a single HTML file works both as an
interactive web page and as the source for the tagged PDF:

  * an interactive Highcharts container (keyboard nav + screen-reader labels + sonify
    button) — shown on screen, hidden in print (WeasyPrint cannot run its JavaScript);
  * a static vector <img> (the SVG from generate_static.py, base64-inlined with a concise
    alt) — hidden on screen, shown in print so the PDF shows a real chart, tagged /Figure
    with /Alt;
  * a real data <table> with <caption>/scope — always shown, the canonical text alternative
    that needs no JavaScript.

scripts/build_html.py inlines the Highcharts libraries once, replaces each <!--CHART id-->
token with build_figure_html(...), and appends the returned init script. This module owns
no I/O beyond reading the vendored libs, the CSVs, and the pre-rendered SVGs.
"""
import base64
import html
import json
import os

from generate_charts import read_csv, build_table, auto_description  # canonical helpers

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib")
STATIC = os.path.join(HERE, "static")
ACCENT = "#7a1f1f"

# Only what an embedded interactive + sonified chart needs (no client-side PDF export libs).
EMBED_LIBS = ["highcharts.js", "accessibility.js", "sonification.js"]


def read_embed_libs():
    """Return the vendored Highcharts libs as <script> tags, to inline once per document."""
    out = []
    for name in EMBED_LIBS:
        path = os.path.join(LIB, name)
        with open(path, encoding="utf-8") as f:
            out.append(f"<script>{f.read()}</script>")
    return "\n".join(out)


def chart_id(entry):
    out = entry.get("out") or entry["csv"]
    return os.path.splitext(os.path.basename(out))[0]


def manifest_by_id(manifest_path=None):
    path = manifest_path or os.path.join(HERE, "charts.json")
    with open(path, encoding="utf-8") as f:
        return {chart_id(e): e for e in json.load(f)}


def _csv_path(entry):
    p = entry["csv"]
    return p if os.path.isabs(p) else os.path.join(HERE, p)


def _build_cfg(entry, cid, desc, cat_name, categories, series):
    chart_type = entry.get("type", "column")
    cfg = {
        "chart": {"type": chart_type, "height": 380},
        "title": {"text": entry.get("title", cid)},
        "subtitle": ({"text": entry["subtitle"]} if entry.get("subtitle") else {}),
        "accessibility": {"description": desc,
                          "point": {"valueDescriptionFormat": "{xDescription}, {value}"}},
        "xAxis": {"categories": categories, "title": {"text": cat_name}},
        "yAxis": {"min": 0,
                  "title": {"text": entry.get("ylabel")
                            or (series[0]["name"] if len(series) == 1 else "Value")}},
        "legend": {"enabled": len(series) > 1},
        "plotOptions": {"series": {"dataLabels": {"enabled": len(series) == 1}}},
        "sonification": {"duration": 4000},
        "credits": {"enabled": False},
        "exporting": {"enabled": False},
        "series": [{"name": s["name"], "data": s["data"],
                    **({"color": ACCENT} if len(series) == 1 else {})} for s in series],
    }
    if entry.get("ymax") is not None:
        cfg["yAxis"]["max"] = entry["ymax"]
    return cfg


def build_figure_html(entry):
    """Return (figure_html, init_js) for one charts.json entry."""
    cid = chart_id(entry)
    cat_name, categories, series = read_csv(_csv_path(entry))
    title = entry.get("title", cid)
    desc = auto_description(title, cat_name, categories, series)
    kind = "Bar chart" if len(series) == 1 else "Grouped bar chart"

    # Static vector fallback (concise alt; the data lives in the caption + table per house style).
    svg_path = os.path.join(STATIC, cid + ".svg")
    static_img = ""
    if os.path.exists(svg_path):
        with open(svg_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        static_alt = html.escape(f"{kind}: {title}. Full values are in the data table that follows.")
        static_img = (f'<img class="chart-static" alt="{static_alt}" '
                      f'src="data:image/svg+xml;base64,{b64}">')

    table = build_table(cat_name, categories, series)
    cap = html.escape(title)
    sub = f' <span class="chart-sub">{html.escape(entry["subtitle"])}</span>' if entry.get("subtitle") else ""

    figure = (
        f'<figure class="chart-figure" role="group" aria-labelledby="cap-{cid}">\n'
        f'  <figcaption id="cap-{cid}"><strong>Accessible chart:</strong> {cap}.{sub} '
        f'An interactive version appears on screen; a static chart and a full data table follow.</figcaption>\n'
        f'  <div class="chart-interactive" id="chart-{cid}"></div>\n'
        f'  <button class="chart-sonify" type="button" data-chart="chart-{cid}">'
        f'&#9654; Play chart as sound</button>\n'
        f'  {static_img}\n'
        f'  <table class="chart-data">\n{table}\n  </table>\n'
        f'</figure>'
    )

    cfg = _build_cfg(entry, cid, desc, cat_name, categories, series)
    # Progressive enhancement: only flip the figure to the interactive view once the chart
    # has actually rendered. If Highcharts is unavailable or throws, the figure keeps its
    # static <img> fallback (and that <img>'s alt is the last resort if the image fails too).
    init_js = (
        f"(function(){{try{{Highcharts.chart('chart-{cid}', "
        f"{json.dumps(cfg, ensure_ascii=False)});"
        f"var el=document.getElementById('chart-{cid}');"
        f"if(el){{var f=el.closest('.chart-figure');if(f){{f.classList.add('chart-ready');}}}}"
        f"}}catch(e){{console.warn('Chart chart-{cid} failed to render',e);}}}})();"
    )
    return figure, init_js
