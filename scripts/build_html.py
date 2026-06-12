#!/usr/bin/env python3
"""
build_html.py — render document/Ring-of-Fire-1994.md into a single self-contained,
accessible HTML file with every image embedded as base64 and wrapped in
<figure>/<figcaption>, the RSP formula exposed via role="math"+aria-label, real
<table> markup, lang="en", and a skip link.

Requires:  pip install markdown   (see requirements.txt)
Usage:     python scripts/build_html.py
"""
import base64, os, re, sys
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "document")
MD = os.path.join(DOC, "Ring-of-Fire-1994.md")
OUT = os.path.join(DOC, "Ring-of-Fire-1994.html")

# Embedded accessible charts (interactive on screen, static SVG in print). See charts/embed.py.
sys.path.insert(0, os.path.join(ROOT, "charts"))
import embed  # noqa: E402

CSS = """
  :root{--ink:#1a1a1a;--rule:#d8d8d8;--accent:#7a1f1f;--bg:#fff;--callout:#f6f4f1;--focus:#0b5fff;}
  *{box-sizing:border-box;}
  body{font-family:Georgia,'Times New Roman',serif;line-height:1.6;color:var(--ink);background:var(--bg);max-width:820px;margin:0 auto;padding:2rem 1.25rem 6rem;}
  .skip{position:absolute;left:-999px;}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;border:2px solid var(--accent);z-index:10;}
  h1{font-size:2.4rem;line-height:1.15;margin:.2em 0 .1em;}
  h2{font-size:1.6rem;margin-top:2.2rem;border-bottom:2px solid var(--rule);padding-bottom:.2em;}
  h3{font-size:1.25rem;margin-top:1.8rem;color:var(--accent);}
  h4{font-size:1.05rem;margin-top:1.4rem;}
  a{color:var(--accent);}
  figure{margin:1.6rem 0;text-align:center;}
  figure img{max-width:100%;height:auto;border:1px solid var(--rule);background:#fff;}
  figcaption{font-size:.95rem;margin-top:.6rem;text-align:left;background:var(--callout);border-left:4px solid var(--accent);padding:.7rem .9rem;}
  blockquote{margin:1.2rem 0;padding:.6rem 1rem;border-left:4px solid var(--accent);background:var(--callout);font-style:italic;color:#333;}
  table{border-collapse:collapse;width:100%;margin:1.2rem 0;font-family:Arial,Helvetica,sans-serif;font-size:.9rem;}
  caption{text-align:left;font-weight:bold;margin-bottom:.4rem;}
  th,td{border:1px solid var(--rule);padding:.4rem .55rem;text-align:left;vertical-align:top;}
  thead th{background:#efe9e4;} tbody tr:nth-child(even){background:#faf8f6;}
  td:not(:first-child){font-variant-numeric:tabular-nums;}
  .formula{font-family:'Cambria Math',Georgia,serif;font-size:1.15rem;text-align:center;background:var(--callout);padding:.7rem;margin:1rem 0;border:1px solid var(--rule);}
  hr{border:0;border-top:1px solid var(--rule);margin:2rem 0;}
  .chart-figure{margin:1.8rem 0;padding:1rem;border:1px solid var(--rule);background:#fff;}
  .chart-figure>figcaption{background:var(--callout);border-left:4px solid var(--accent);padding:.7rem .9rem;margin-bottom:.8rem;font-size:.95rem;text-align:left;font-family:Arial,Helvetica,sans-serif;}
  .chart-sub{display:block;color:#555;font-size:.85rem;margin-top:.25rem;}
  /* Fallback chain (screen): interactive chart -> static image -> the image's alt text.
     The interactive view and sonify control stay hidden until JS confirms the chart
     rendered (figure gets .chart-ready); otherwise the static SVG <img> is shown. */
  .chart-interactive{min-height:380px;display:none;}
  .chart-static{display:block;max-width:100%;height:auto;margin:.4rem auto;}
  .chart-sonify{display:none;font:inherit;font-family:Arial,Helvetica,sans-serif;font-size:.9rem;padding:.45rem .8rem;border:1px solid var(--accent);background:#fff;color:var(--accent);border-radius:6px;cursor:pointer;margin:.5rem 0;}
  .chart-sonify:hover,.chart-sonify:focus{background:var(--accent);color:#fff;}
  .chart-figure.chart-ready .chart-interactive{display:block;}
  .chart-figure.chart-ready .chart-sonify{display:inline-block;}
  .chart-figure.chart-ready .chart-static{display:none;}
  .chart-data{max-width:560px;}
  @media print{
    body{max-width:none;}
    .chart-interactive,.chart-sonify{display:none !important;}
    .chart-static{display:block !important;}
  }
"""

def datauri(relpath):
    with open(os.path.join(DOC, relpath), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

def inline_html(md_text):
    h = markdown.markdown(md_text.strip())
    return re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.DOTALL).strip()

def main():
    src = open(MD, encoding="utf-8").read()
    lines = src.split("\n")
    img_re = re.compile(r"^!\[(?P<alt>.*)\]\((?P<src>images/[^)]+)\)\s*$")
    chart_re = re.compile(r"^<!--\s*CHART\s+(?P<id>[A-Za-z0-9_-]+)\s*-->\s*$")
    chart_manifest = embed.manifest_by_id()
    figures, charts, out, i = [], [], [], 0
    while i < len(lines):
        cm = chart_re.match(lines[i])
        if cm:
            cid = cm.group("id")
            entry = chart_manifest.get(cid)
            if entry is None:
                raise SystemExit(f"Unknown chart id in <!--CHART {cid}--> (not in charts/charts.json)")
            fig_html, init_js = embed.build_figure_html(entry)
            charts.append((fig_html, init_js))
            out += ["", f"CHARTTOKEN{len(charts)-1}ENDCHART", ""]
            i += 1
            continue
        m = img_re.match(lines[i])
        if m:
            alt, srcp = m.group("alt"), m.group("src")
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            cap = None
            if j < len(lines) and lines[j].lstrip().startswith(">"):
                cl, k = [], j
                while k < len(lines) and (lines[k].lstrip().startswith(">") or
                        (cl and lines[k].strip() == "" and k + 1 < len(lines) and lines[k+1].lstrip().startswith(">"))):
                    cl.append(re.sub(r"^\s*>\s?", "", lines[k])); k += 1
                cap = "\n".join(cl).strip(); i = k
            else:
                i += 1
            img = f'<img alt="{alt.replace(chr(34), "&quot;")}" src="{datauri(srcp)}" loading="lazy">'
            figures.append(f"<figure>{img}<figcaption>{inline_html(cap)}</figcaption></figure>" if cap
                           else f"<figure>{img}</figure>")
            out += ["", f"FIGTOKEN{len(figures)-1}ENDFIG", ""]
            continue
        out.append(lines[i]); i += 1

    body = "\n".join(out)
    body = body.replace(r"$$\mathrm{RSP} = E \times A \times k$$", "FORMULATOKEN1")
    body = re.sub(r"\$\$\\frac.*?\\approx 82\$\$", "FORMULATOKEN2", body, flags=re.DOTALL)
    h = markdown.markdown(body, extensions=["tables", "sane_lists", "attr_list", "toc"])
    for n, fig in enumerate(figures):
        h = h.replace(f"<p>FIGTOKEN{n}ENDFIG</p>", fig).replace(f"FIGTOKEN{n}ENDFIG", fig)
    for n, (fig_html, _init) in enumerate(charts):
        h = h.replace(f"<p>CHARTTOKEN{n}ENDCHART</p>", fig_html).replace(f"CHARTTOKEN{n}ENDCHART", fig_html)
    h = h.replace("<p>FORMULATOKEN1</p>",
        '<div class="formula" role="math" aria-label="R S P equals E times A times k">RSP = <i>E</i> &times; <i>A</i> &times; <i>k</i></div>')
    h = h.replace("<p>FORMULATOKEN2</p>",
        '<div class="formula" role="math" aria-label="The quantity 185 times 1000 squared, divided by 450240, '
        'times the quantity 0.45 squared times 0.7854, times 1.25, approximately equals 82">'
        '(185 &times; 1,000<sup>2</sup>) &divide; 450,240 &times; (0.45<sup>2</sup> &times; 0.7854) &times; 1.25 &approx; 82</div>')

    # Inline the Highcharts libraries once, and emit one init + sonify-wiring script,
    # only when the document actually embeds charts.
    chart_libs = chart_script = ""
    if charts:
        chart_libs = "\n" + embed.read_embed_libs()
        inits = "\n  ".join(init for _f, init in charts)
        chart_script = (
            '\n<script>\ndocument.addEventListener("DOMContentLoaded", function () {\n  '
            + inits +
            '\n  document.querySelectorAll(".chart-sonify").forEach(function (btn) {\n'
            '    btn.addEventListener("click", function () {\n'
            '      var c = (Highcharts.charts || []).find(function (ch) {\n'
            '        return ch && ch.renderTo && ch.renderTo.id === btn.dataset.chart; });\n'
            '      if (c) { try { c.sonify(); } catch (e) { console.warn(e); } }\n'
            '    });\n  });\n});\n</script>'
        )

    # Defense-in-depth CSP: the document is fully self-contained (everything inlined; images
    # are data: URIs) and the vendored Highcharts uses no eval/Function, so this strict policy
    # works as-is while blocking ALL network egress — no external fetch, no data exfiltration.
    csp = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
           "script-src 'unsafe-inline'; font-src data:; base-uri 'none'; form-action 'none'")
    doc = (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           f'<meta http-equiv="Content-Security-Policy" content="{csp}">\n'
           f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           f'<title>Ring of Fire: The Handgun Makers of Southern California (1994)</title>\n'
           f"<style>{CSS}</style>{chart_libs}\n</head>\n<body>\n"
           f'<a class="skip" href="#main">Skip to content</a>\n<main id="main">\n{h}\n</main>\n'
           f'{chart_script}\n</body>\n</html>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"Wrote {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB) | figures={doc.count('<figure>')} "
          f"figcaptions={doc.count('<figcaption>')} charts={len(charts)} "
          f"empty_alts={len(re.findall(chr(97)+'lt='+chr(34)+chr(34), doc))}")

if __name__ == "__main__":
    main()
