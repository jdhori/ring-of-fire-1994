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

# A diagram id carries no figure number, so map it to the source figure it makes accessible.
DIAGRAM_FIGURE = {"family-tree": "Figure 1-1"}


def figure_label(cid):
    """Human figure reference from a chart/table id: 'figure-2-2' -> 'Figure 2-2',
    'table-4-2' -> 'Table 4-2', 'figure-1-1' -> 'Figure 1-1'."""
    parts = cid.split("-")
    return f"{parts[0].capitalize()} {'-'.join(parts[1:])}" if len(parts) > 1 else cid


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


def _read_mmd_acc(path):
    """Pull accTitle / accDescr out of a Mermaid source so the title and the long text
    description stay single-sourced in the .mmd (where they also become SVG <title>/<desc>)."""
    title = descr = ""
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("accTitle:"):
                title = s[len("accTitle:"):].strip()
            elif s.startswith("accDescr:"):
                descr = s[len("accDescr:"):].strip()
    return title, descr


def build_mermaid_html(diagram_id):
    """Return an accessible <figure> for a rendered Mermaid diagram (e.g. the family tree).

    Unlike the data charts, a diagram has no interactive layer: the pre-rendered SVG
    (htmlLabels:false, so its labels are native <text> — see render_diagrams.py) is shown the
    same way on screen and in print, base64-inlined as an <img> (inert: an <img> never runs
    SVG script, and it gets a /Figure + /Alt tag in the PDF). The figcaption carries the full
    text description from the .mmd's accDescr; the adjacent data table is the tabular alternative.
    """
    mmd_path = os.path.join(HERE, diagram_id + ".mmd")
    svg_path = os.path.join(STATIC, diagram_id + ".svg")
    title, descr = _read_mmd_acc(mmd_path)
    with open(svg_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    flabel = DIAGRAM_FIGURE.get(diagram_id, "")
    lead = f"{flabel} \u2014 accessible diagram" if flabel else "Accessible diagram"
    ref = f"{flabel}: " if flabel else ""
    alt = html.escape(f"Accessible diagram of {ref}{title}. A full text description is in "
                      f"the caption, and the figure's data table appears alongside it.")
    cap = html.escape(title) if title else diagram_id
    long_desc = html.escape(descr)
    return (
        f'<figure class="diagram-figure" role="group" aria-labelledby="dgm-{diagram_id}">\n'
        f'  <figcaption id="dgm-{diagram_id}"><strong>{lead}:</strong> {cap}. '
        f'<span class="diagram-desc">{long_desc}</span></figcaption>\n'
        f'  <img class="diagram-img" alt="{alt}" src="data:image/svg+xml;base64,{b64}">\n'
        f'</figure>'
    )


def build_figure_html(entry):
    """Return (figure_html, init_js) for one charts.json entry."""
    cid = chart_id(entry)
    flabel = figure_label(cid)
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
        static_alt = html.escape(f"{kind} of {flabel}: {title}. Full values are in the data table.")
        static_img = (f'<img class="chart-static" alt="{static_alt}" '
                      f'src="data:image/svg+xml;base64,{b64}">')

    table = build_table(cat_name, categories, series)
    cap = html.escape(title)
    sub = f' <span class="chart-sub">{html.escape(entry["subtitle"])}</span>' if entry.get("subtitle") else ""

    figure = (
        f'<figure class="chart-figure" role="group" aria-labelledby="cap-{cid}">\n'
        f'  <figcaption id="cap-{cid}"><strong>{flabel} \u2014 accessible chart:</strong> {cap}.{sub} '
        f'An interactive version appears on screen; a static chart and the data table (below) follow.</figcaption>\n'
        f'  <div class="chart-interactive" id="chart-{cid}"></div>\n'
        f'  <button class="chart-sonify" type="button" data-chart="chart-{cid}">'
        f'&#9654; Play chart as sound</button>\n'
        f'  {static_img}\n'
        f'  <details class="data-details"><summary>Show the data table for {flabel}</summary>\n'
        f'  <div class="data-body"><table class="chart-data">\n{table}\n  </table></div>\n'
        f'  </details>\n'
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
