#!/usr/bin/env python3
"""
generate_static.py — render each chart in charts.json to a static, accessible SVG.

The interactive Highcharts widgets (generate_charts.py) need a browser + JavaScript, so
they cannot render into a printed/PDF deliverable. WeasyPrint (scripts/build_pdf.py) does
not execute JS. This script produces a browserless *vector* fallback — one SVG per chart,
via Altair / Vega-Lite + vl-convert (the project's sanctioned scripted-export path) — so the
PDF edition shows a real chart instead of an empty container. The exact numbers always also
travel in the data <table> that scripts/build_html.py emits beside the chart.

Single-series CSVs -> one bar series (accent fill). Multi-series CSVs -> grouped bars with a
legend; series are distinguished by position (grouping) + legend label + the data table, not
by color alone.

Output: charts/static/<csv-stem>.svg  (stem matches the chart id used in <!--CHART id-->).

Requires:  pip install altair vl-convert-python pandas   (see requirements.txt)
Usage:     python charts/generate_static.py            # all charts in charts.json
"""
import json
import os

import altair as alt
import pandas as pd
import vl_convert as vlc

from generate_charts import read_csv  # reuse the canonical CSV reader

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "static")
ACCENT = "#7a1f1f"
SERIES_COLORS = [ACCENT, "#2f5d8a", "#6b6b6b"]  # accent + distinct, high-contrast hues
WIDTH, HEIGHT = 600, 360


def chart_id(entry):
    out = entry.get("out") or entry["csv"]
    return os.path.splitext(os.path.basename(out))[0]


def build_spec(entry):
    csv_path = entry["csv"]
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(HERE, csv_path)
    cat_name, categories, series = read_csv(csv_path)
    title = entry.get("title", chart_id(entry))
    subtitle = entry.get("subtitle", "")
    ylabel = entry.get("ylabel") or (series[0]["name"] if len(series) == 1 else "Value")

    title_cfg = alt.TitleParams(
        text=_wrap(title, 64),
        subtitle=_wrap(subtitle, 78) if subtitle else "",
        anchor="start", fontSize=15, subtitleFontSize=11, subtitleColor="#555",
    )
    x_enc = alt.X(f"{cat_name}:N", sort=categories, title=cat_name,
                  axis=alt.Axis(labelAngle=0))

    if len(series) == 1:
        df = pd.DataFrame({cat_name: categories, ylabel: series[0]["data"]})
        chart = (
            alt.Chart(df, title=title_cfg, width=WIDTH, height=HEIGHT)
            .mark_bar(color=ACCENT)
            .encode(x=x_enc, y=alt.Y(f"{ylabel}:Q", title=ylabel),
                    tooltip=[cat_name, ylabel])
        )
    else:
        rows = []
        for s in series:
            for cat, val in zip(categories, s["data"]):
                rows.append({cat_name: cat, "Series": s["name"], "Value": val})
        df = pd.DataFrame(rows)
        names = [s["name"] for s in series]
        chart = (
            alt.Chart(df, title=title_cfg, width=WIDTH, height=HEIGHT)
            .mark_bar()
            .encode(
                x=x_enc,
                xOffset=alt.XOffset("Series:N", sort=names),
                y=alt.Y("Value:Q", title=ylabel),
                color=alt.Color("Series:N", sort=names,
                                scale=alt.Scale(domain=names, range=SERIES_COLORS[:len(names)]),
                                legend=alt.Legend(title=None, orient="top")),
                tooltip=[cat_name, "Series", "Value"],
            )
        )

    spec = chart.to_dict()
    spec["description"] = entry.get("title", chart_id(entry))
    spec["config"] = {**spec.get("config", {}),
                      "background": "#ffffff",
                      "view": {"stroke": None},
                      "font": "Arial, Helvetica, sans-serif"}
    return spec


def _wrap(text, width):
    """Soft-wrap a long title into a list of lines for Vega-Lite multi-line titles."""
    if not text or len(text) <= width:
        return text
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur.strip())
            cur = w
        else:
            cur += " " + w
    if cur.strip():
        lines.append(cur.strip())
    return lines


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(HERE, "charts.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    for entry in manifest:
        cid = chart_id(entry)
        svg = vlc.vegalite_to_svg(build_spec(entry))
        out = os.path.join(OUT_DIR, cid + ".svg")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {os.path.relpath(out, HERE)} ({len(svg)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
