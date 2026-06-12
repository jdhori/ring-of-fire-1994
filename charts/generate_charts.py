#!/usr/bin/env python3
"""
generate_charts.py — turn a CSV into a self-contained, accessible chart.

Each output is ONE HTML file that needs no internet and provides the same data
three independent ways (the layered accessibility pattern this project standardised on):

  1. an interactive Highcharts chart (keyboard-navigable, per-point screen-reader labels),
  2. an audio "sonification" of the series, and
  3. a real <table> text alternative (works even with scripting disabled).

All JavaScript (Highcharts + accessibility / sonification / exporting modules and the
jsPDF + svg2pdf libraries used for offline PDF export) is inlined from ./lib so the
result is fully portable. Highcharts is free for personal / non-commercial use; verify
licensing before any commercial deployment (see CLAUDE.md).

CSV format
----------
First column  = category label (x axis).
Remaining columns = one or more numeric series (the header is the series name).
  Caliber,Share of U.S. production (%)
  .22,36
  .25 ACP,83
  ...

Usage
-----
Single chart:
  python generate_charts.py data/figure-2-2_caliber-share.csv \
      --title "Ring of Fire share of total U.S. pistol production, by caliber, 1992" \
      --subtitle "Source: Wintemute, Ring of Fire (1994), Figure 2-2" \
      --ylabel "Share of U.S. pistol production (%)" --ymax 100 \
      --out out/figure-2-2.html

Batch (recommended for the whole report):
  python generate_charts.py --manifest charts.json
"""
import argparse, csv, json, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib")
ACCENT = "#7a1f1f"

LIB_FILES = [
    "jspdf.umd.min.js", "svg2pdf.umd.min.js",
    "highcharts.js", "exporting.js", "offline-exporting.js",
    "accessibility.js", "sonification.js",
]


def read_libs():
    out = []
    for name in LIB_FILES:
        path = os.path.join(LIB, name)
        if not os.path.exists(path):
            sys.exit(f"Missing vendored library: {path}\n"
                     "Re-vendor from the 'highcharts', 'jspdf', and 'svg2pdf.js' npm packages.")
        with open(path, encoding="utf-8") as f:
            out.append(f"<script>{f.read()}</script>")
    return "\n".join(out)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    cat_name, series_names = header[0], header[1:]
    categories = [r[0] for r in rows[1:]]
    series = []
    for i, name in enumerate(series_names, start=1):
        series.append({"name": name, "data": [float(r[i]) for r in rows[1:]]})
    return cat_name, categories, series


def fmt_num(v):
    return str(int(v)) if float(v).is_integer() else str(v)


def auto_description(title, cat_name, categories, series):
    kind = "Bar chart" if len(series) == 1 else "Grouped bar chart"
    parts = [f"{kind} titled {title}."]
    for s in series:
        pairs = ", ".join(f"{c} {fmt_num(v)}" for c, v in zip(categories, s["data"]))
        lead = "Values" if len(series) == 1 else s["name"]
        parts.append(f"{lead}: {pairs}.")
    parts.append("A full data table follows the chart.")
    return " ".join(parts)


def build_table(cat_name, categories, series):
    head = "".join(f'<th scope="col">{html.escape(s["name"])}</th>' for s in series)
    body = []
    for i, c in enumerate(categories):
        cells = "".join(f"<td>{fmt_num(s['data'][i])}</td>" for s in series)
        body.append(f'        <tr><th scope="row">{html.escape(c)}</th>{cells}</tr>')
    return (
        f'    <caption>{html.escape("Data: " + cat_name)}</caption>\n'
        f'    <thead><tr><th scope="col">{html.escape(cat_name)}</th>{head}</tr></thead>\n'
        f"    <tbody>\n" + "\n".join(body) + "\n    </tbody>"
    )


def build_html(csv_path, title, subtitle, ylabel, ymax, chart_type):
    cat_name, categories, series = read_csv(csv_path)
    if not title:
        title = os.path.splitext(os.path.basename(csv_path))[0].replace("_", " ")
    desc = auto_description(title, cat_name, categories, series)

    cfg = {
        "chart": {"type": chart_type, "width": 760, "height": 440},
        "title": {"text": title},
        "subtitle": {"text": subtitle} if subtitle else {},
        "accessibility": {"description": desc, "point": {"valueDescriptionFormat": "{xDescription}, {value}"}},
        "xAxis": {"categories": categories, "title": {"text": cat_name}},
        "yAxis": {"min": 0, "title": {"text": ylabel or (series[0]["name"] if len(series) == 1 else "Value")}},
        "legend": {"enabled": len(series) > 1},
        "plotOptions": {"series": {"dataLabels": {"enabled": len(series) == 1}}},
        "sonification": {"duration": 4000},
        "exporting": {"enabled": True, "fallbackToExportServer": False,
                      "buttons": {"contextButton": {"menuItems":
                          ["downloadPNG", "downloadJPEG", "downloadSVG", "downloadPDF"]}}},
        "series": [{"name": s["name"], "data": s["data"],
                    **({"color": ACCENT} if len(series) == 1 else {})} for s in series],
    }
    if ymax is not None:
        cfg["yAxis"]["max"] = ymax
    cfg_json = json.dumps(cfg, ensure_ascii=False)

    table = build_table(cat_name, categories, series)
    libs = read_libs()
    esc_title = html.escape(title)
    esc_desc = html.escape(desc)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc_title}</title>
<style>
  body{{font-family:Georgia,serif;max-width:860px;margin:0 auto;padding:2rem 1.25rem 4rem;color:#1a1a1a;line-height:1.6;}}
  h1{{font-size:1.6rem;}}
  .note{{font-size:.85rem;color:#555;font-family:Arial,sans-serif;}}
  .summary{{background:#f6f4f1;border-left:4px solid {ACCENT};padding:.7rem 1rem;}}
  #container{{min-height:440px;}}
  button{{font:inherit;font-family:Arial,sans-serif;padding:.45rem .8rem;border:1px solid {ACCENT};background:#fff;color:{ACCENT};border-radius:6px;cursor:pointer;margin-top:.5rem;}}
  details{{margin-top:1rem;}} summary{{cursor:pointer;font-family:Arial,sans-serif;font-weight:bold;}}
  table{{border-collapse:collapse;width:100%;max-width:640px;margin:.75rem 0;font-family:Arial,sans-serif;font-size:.92rem;}}
  caption{{text-align:left;font-weight:bold;margin-bottom:.4rem;}}
  th,td{{border:1px solid #d8d8d8;padding:.4rem .6rem;text-align:left;}}
  th[scope=col]{{background:#efe9e4;}} td{{text-align:right;font-variant-numeric:tabular-nums;}}
  .sr-only{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;}}
</style>
{libs}
</head>
<body>
<h1>{esc_title}</h1>
<p class="note">Self-contained: all chart code is embedded, no internet required.</p>
<p class="summary" id="chart-desc">{esc_desc}</p>

<figure role="group" aria-labelledby="chart-h" aria-describedby="chart-desc">
  <figcaption id="chart-h" class="sr-only">{esc_title}</figcaption>
  <div id="container"></div>
  <button id="play" type="button">&#9654; Play as sound</button>
</figure>

<details open>
  <summary>Data table (text alternative)</summary>
  <table>
{table}
  </table>
</details>

<p class="note">Keyboard: Tab into the chart, then arrow keys move between points. The export
menu (top-right) writes PNG / JPEG / SVG / PDF locally. The data table above is the canonical
text alternative and works with scripting disabled.</p>

<script>
document.addEventListener('DOMContentLoaded', function () {{
  var chart = Highcharts.chart('container', {cfg_json});
  var btn = document.getElementById('play');
  if (btn) btn.addEventListener('click', function () {{ try {{ chart.sonify(); }} catch (e) {{ console.warn(e); }} }});
}});
</script>
</body>
</html>"""


def write(out_path, content):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote {out_path} ({len(content)/1024:.0f} KB)")


def main():
    ap = argparse.ArgumentParser(description="Generate self-contained accessible charts from CSV.")
    ap.add_argument("csv", nargs="?", help="input CSV (category in column 1, one or more series after)")
    ap.add_argument("--title", default="")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--ylabel", default="")
    ap.add_argument("--ymax", type=float, default=None)
    ap.add_argument("--type", dest="chart_type", default="column", choices=["column", "bar", "line", "spline"])
    ap.add_argument("--out", default="")
    ap.add_argument("--manifest", help="JSON file: list of {csv,title,subtitle,ylabel,ymax,type,out}")
    args = ap.parse_args()

    if args.manifest:
        with open(args.manifest, encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            csv_path = it["csv"] if os.path.isabs(it["csv"]) else os.path.join(HERE, it["csv"])
            out = it.get("out") or os.path.join("out", os.path.splitext(os.path.basename(csv_path))[0] + ".html")
            out = out if os.path.isabs(out) else os.path.join(HERE, out)
            write(out, build_html(csv_path, it.get("title", ""), it.get("subtitle", ""),
                                  it.get("ylabel", ""), it.get("ymax"), it.get("type", "column")))
        return

    if not args.csv:
        ap.error("provide a CSV path or --manifest")
    out = args.out or os.path.join("out", os.path.splitext(os.path.basename(args.csv))[0] + ".html")
    write(out, build_html(args.csv, args.title, args.subtitle, args.ylabel, args.ymax, args.chart_type))


if __name__ == "__main__":
    main()
