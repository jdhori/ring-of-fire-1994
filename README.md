# Ring of Fire (1994) — accessible digital edition

A faithful, accessible, modern digital edition of *Ring of Fire: The Handgun Makers of
Southern California* (Garen J. Wintemute, UC Davis Violence Prevention Research Program,
1994), rebuilt from a 112-page print-locked scanned PDF.

## What's here

- **`document/Ring-of-Fire-1994.md`** — clean Markdown of the full report (generated from
  the section files in `build/`). Convert with Pandoc to docx/EPUB/etc.
- **`document/Ring-of-Fire-1994.html`** — a single self-contained, accessible HTML edition:
  every image embedded, `<figure>`/`<figcaption>` with descriptive alt text, real tables,
  `lang`, skip link, the Relative Stopping Power formula exposed to assistive tech, and four
  exact-data charts embedded inline as interactive Highcharts (keyboard nav + sonification +
  data table).
- **`document/Ring-of-Fire-1994.pdf`** — a tagged, accessible **PDF/UA-1** edition rendered
  from the HTML (WeasyPrint): full tag tree, heading/table structure, per-figure `/Alt`
  text, `/Lang`, displayed document title, and PDF outline bookmarks. The interactive charts
  become static vector (SVG) figures plus their data tables here, since a PDF runs no JS.
- **`document/images/`** — 25 cropped figures (cover, family tree, all of Figures 2-1…2-23).
- **`charts/`** — a generator that turns CSV data into self-contained, accessible interactive
  charts (Highcharts + keyboard nav + sonification + a `<table>` alternative), a static-SVG
  fallback exporter for print/PDF (Altair/vl-convert), the embed helper that drops both into
  the editions, plus a five-way comparison of charting approaches and a Mermaid family tree.

## Quickstart

```bash
pip install -r requirements.txt   # markdown + weasyprint (PDF needs system pango/cairo)

# Export — pick the format(s) you need:
make md        # -> document/Ring-of-Fire-1994.md   (Markdown)
make html      # -> document/Ring-of-Fire-1994.html  (self-contained accessible HTML)
make pdf       # -> document/Ring-of-Fire-1994.pdf   (tagged accessible PDF/UA-1)
make export    # all three in one pass

make charts        # generate every standalone chart in charts/charts.json into charts/out/
make charts-static # regenerate the static SVG fallbacks embedded in the HTML/PDF editions
```

`make html` and `make pdf` rebuild the static chart fallbacks first, so the embedded charts
always reflect the CSVs in `charts/data/`.

`make doc` remains as a back-compat alias for `make html`.

To edit the report text, change the ordered section files in **`build/`** and re-export.
Do not edit `document/Ring-of-Fire-1994.md` directly — it is regenerated.

The PDF is produced from the accessible HTML, so its accessibility tracks the HTML's. To
convert the Markdown to still other formats, use Pandoc, e.g.:

```bash
pandoc document/Ring-of-Fire-1994.md -o Ring-of-Fire-1994.docx   # keep document/images/ alongside
```

## Working rules

See **`CLAUDE.md`** for the full project rules. The essentials: the edition is a *faithful*
1994 transcription (no fabricated or modernized data; original errors preserved as printed),
and accessibility (WCAG 2.2 AA) is a hard requirement on every deliverable.

## Notes

- The source PDF is fully scanned (no text layer); figures were cropped from page renders and
  table/figure values transcribed by reading the page images (OCR garbles tabular content).
- Highcharts is vendored in `charts/lib/` and is free for personal/non-commercial use — verify
  licensing before any commercial deployment.
- Charts are embedded next to (never in place of) the original cropped scans/tables, keyed by
  `<!--CHART id-->` tokens in the `build/` sources. Each is shown three ways — interactive
  chart, sonification, and a real data table — so the same data is available on screen, in the
  tagged PDF, and with scripting disabled. See the Charts section of `CLAUDE.md` to add more.
