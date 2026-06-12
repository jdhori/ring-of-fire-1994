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
  /* Mermaid diagram (e.g. Figure 1-1 family tree): the same accessible vector is shown on
     screen and in print; the figcaption carries the long text description, the adjacent
     table is the tabular alternative. */
  .diagram-figure{margin:1.8rem 0;padding:1rem;border:1px solid var(--rule);background:#fff;}
  .diagram-figure>figcaption{background:var(--callout);border-left:4px solid var(--accent);padding:.7rem .9rem;margin-bottom:.8rem;font-size:.95rem;text-align:left;font-family:Arial,Helvetica,sans-serif;}
  .diagram-desc{display:block;color:#555;font-size:.85rem;margin-top:.4rem;}
  .diagram-img{display:block;max-width:100%;height:auto;margin:.4rem auto;}
  /* Collapsible disclosures: the original raster scan, and figure data tables. The accessible
     content (descriptive caption / interactive chart / vector diagram) leads; the historic scan
     and the data table are tucked into native, keyboard-accessible <details> a reader can expand
     to verify the accessible edition against the source. */
  .scan-figure{margin:1.6rem 0;text-align:left;}
  details.scan,details.data-details{border:1px solid var(--rule);border-radius:6px;background:#faf8f6;margin:.6rem 0;}
  details.scan>summary,details.data-details>summary{cursor:pointer;list-style:none;padding:.5rem .8rem;font-family:Arial,Helvetica,sans-serif;font-size:.9rem;font-weight:bold;color:var(--accent);}
  details.scan>summary::-webkit-details-marker,details.data-details>summary::-webkit-details-marker{display:none;}
  details.scan>summary::before,details.data-details>summary::before{content:"\u25B6";display:inline-block;margin-right:.5rem;font-size:.8em;}
  details.scan[open]>summary::before,details.data-details[open]>summary::before{content:"\u25BC";}
  details.scan>summary:hover,details.data-details>summary:hover{text-decoration:underline;}
  details.scan>summary:focus-visible,details.data-details>summary:focus-visible{outline:2px solid var(--focus);outline-offset:2px;}
  .scan-body{padding:.6rem;text-align:center;}
  .data-body{padding:.2rem .6rem .6rem;}
  .data-body>table,.data-body>.chart-data{margin:.4rem 0;}
  @media print{
    body{max-width:none;}
    .chart-interactive,.chart-sonify{display:none !important;}
    .chart-static{display:block !important;}
    /* keep historic scans and data tables in the PDF; drop the now-meaningless toggle chrome */
    details{border:0 !important;background:none !important;}
    details>summary{display:none !important;}
    details>*:not(summary){display:block !important;}
  }
"""

def datauri(relpath):
    with open(os.path.join(DOC, relpath), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

def inline_html(md_text):
    # Captions are usually a single prose paragraph, but Figure 1-1's caption embeds the
    # family-tree data table (a markdown table inside the blockquote), so render with the
    # tables/sane_lists extensions and only unwrap the <p> when the whole caption is one
    # paragraph — otherwise leave the block-level HTML (e.g. the <table>) intact and valid.
    h = markdown.markdown(md_text.strip(), extensions=["tables", "sane_lists"])
    unwrapped = re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.DOTALL)
    return (unwrapped if "<p>" not in unwrapped and "</p>" not in unwrapped else h).strip()

FIG_LABEL_RE = re.compile(r"fig-(\d+)-(\d+)")
TABLE_RE = re.compile(r"<table\b.*?</table>", re.DOTALL)

def split_caption_table(cap_html):
    """Separate a <table> (a figure's embedded data table) from the rest of the caption HTML,
    so the prose description can stay a visible figcaption while the table moves into its own
    collapsible disclosure. Returns (prose_html, table_html); table_html is "" if none."""
    m = TABLE_RE.search(cap_html)
    if not m:
        return cap_html, ""
    return (cap_html[:m.start()] + cap_html[m.end():]).strip(), m.group(0)

def build_figure(srcp, img, cap):
    """Build a <figure> for an original scanned image.

    The cover stays plain. For every numbered figure scan the historic raster image
    leads as a collapsed <details> accordion (a reader expands it to verify the
    accessible edition against the 1994 original), followed by the visible descriptive
    figcaption. If the caption embeds a data table (e.g. Figure 1-1's family-tree
    table), that table is pulled out into its own collapsible disclosure so the visible
    caption stays a short description. WeasyPrint renders <details> content regardless
    of state, so both the scan and the data table still appear in the tagged PDF;
    print CSS hides the summaries there to keep the page clean.
    """
    cap_html = inline_html(cap) if cap else ""
    m = FIG_LABEL_RE.search(srcp)
    if not m:  # cover (and any non-numbered image): keep plain, always visible
        figcap = f"<figcaption>{cap_html}</figcaption>" if cap_html else ""
        return f"<figure>{img}{figcap}</figure>"
    label = f"Figure {m.group(1)}-{m.group(2)}"
    prose, table_html = split_caption_table(cap_html)
    scan = (f'<details class="scan"><summary>Show the original 1994 scan of {label}</summary>'
            f'<div class="scan-body">{img}</div></details>')
    figcap = f"<figcaption>{prose}</figcaption>" if prose else ""
    data = (f'<details class="data-details"><summary>Show the data table for {label}</summary>'
            f'<div class="data-body">{table_html}</div></details>') if table_html else ""
    return f'<figure class="scan-figure">{scan}{figcap}{data}</figure>'

def main():
    src = open(MD, encoding="utf-8").read()
    lines = src.split("\n")
    img_re = re.compile(r"^!\[(?P<alt>.*)\]\((?P<src>images/[^)]+)\)\s*$")
    chart_re = re.compile(r"^<!--\s*CHART\s+(?P<id>[A-Za-z0-9_-]+)\s*-->\s*$")
    mermaid_re = re.compile(r"^<!--\s*MERMAID\s+(?P<id>[A-Za-z0-9_-]+)\s*-->\s*$")
    chart_manifest = embed.manifest_by_id()
    figures, charts, diagrams, out, i = [], [], [], [], 0
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
        dm = mermaid_re.match(lines[i])
        if dm:
            did = dm.group("id")
            svg = os.path.join(ROOT, "charts", "static", did + ".svg")
            if not os.path.exists(svg):
                raise SystemExit(f"Missing diagram SVG for <!--MERMAID {did}--> "
                                 f"(run `make diagrams` to render charts/static/{did}.svg)")
            diagrams.append(embed.build_mermaid_html(did))
            out += ["", f"DIAGRAMTOKEN{len(diagrams)-1}ENDDIAGRAM", ""]
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
            figures.append(build_figure(srcp, img, cap))
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
    for n, dgm in enumerate(diagrams):
        h = h.replace(f"<p>DIAGRAMTOKEN{n}ENDDIAGRAM</p>", dgm).replace(f"DIAGRAMTOKEN{n}ENDDIAGRAM", dgm)
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
