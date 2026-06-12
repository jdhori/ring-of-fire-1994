#!/usr/bin/env python3
"""
build_pdf.py — render the self-contained accessible HTML edition into a tagged,
PDF/UA-1 accessible PDF.

It reuses document/Ring-of-Fire-1994.html (produced by build_html.py), which already
carries the accessibility structure we need in the PDF: real headings, <figure>/
<figcaption>, descriptive non-empty image alt, real <table> markup, lang="en", and the
RSP formula exposed via role="math"+aria-label. WeasyPrint carries that semantic
structure into the PDF's tag tree, then `pdf_variant="pdf/ua-1"` enforces PDF/UA-1
(tagged, document title shown, language set).

On top of the HTML we add a print-only stylesheet for page setup (Letter size, margins,
running header, "page X of Y"), heading bookmarks (PDF outline), and break rules so
figures and table rows are not split across pages. Document metadata (author, subject,
keywords) is injected as <meta> tags so the PDF Document Information dictionary is
populated for PDF/UA.

Requires:  pip install weasyprint   (see requirements.txt; needs system pango/cairo)
Usage:     python scripts/build_pdf.py
"""
import os
import re

from weasyprint import HTML, CSS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "document")
HTML_IN = os.path.join(DOC, "Ring-of-Fire-1994.html")
PDF_OUT = os.path.join(DOC, "Ring-of-Fire-1994.pdf")

TITLE = "Ring of Fire: The Handgun Makers of Southern California (1994)"

# PDF/UA wants the Document Information dictionary populated; WeasyPrint reads these
# from <meta> tags in the HTML head. The HTML edition does not carry them, so inject.
META = (
    '<meta name="author" content="Garen J. Wintemute, MD, MPH — '
    'UC Davis Violence Prevention Research Program">\n'
    '<meta name="description" content="Faithful, accessible digital edition of the '
    '1994 public-health policy report Ring of Fire: The Handgun Makers of Southern '
    'California.">\n'
    '<meta name="keywords" content="public health, firearms policy, '
    'Saturday night special, Ring of Fire, 1994, Wintemute">\n'
    '<meta name="dcterms.created" content="1994">\n'
)

# Print-only stylesheet: page geometry, running header + page numbers, PDF outline
# bookmarks from headings, and break rules so figures/tables stay intact.
PRINT_CSS = """
@page {
  size: Letter;
  margin: 22mm 18mm 20mm;
  @top-center {
    content: "Ring of Fire \\2014 The Handgun Makers of Southern California (1994)";
    font: 9pt Georgia, 'Times New Roman', serif; color: #6b6b6b;
  }
  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font: 9pt Georgia, 'Times New Roman', serif; color: #6b6b6b;
  }
}
@page :first { @top-center { content: none; } }

/* PDF outline / bookmarks from the heading hierarchy. */
h1 { bookmark-level: 1; bookmark-label: content(text); string-set: doctitle content(text); }
h2 { bookmark-level: 2; bookmark-label: content(text); }
h3 { bookmark-level: 3; bookmark-label: content(text); }

/* Keep accessible structures intact across page breaks. */
figure, img, tr { break-inside: avoid; }
table { break-inside: auto; }
thead { display: table-header-group; }
h1, h2, h3, h4, caption, figcaption { break-after: avoid; }
h2, h3 { break-before: auto; }

/* Print fit: the screen stylesheet caps the body at 820px; let it use the page. */
body { max-width: none; margin: 0; padding: 0; }
figure img { max-width: 100%; height: auto; }
a { color: #7a1f1f; }
"""


def main():
    if not os.path.exists(HTML_IN):
        raise SystemExit(f"Missing {HTML_IN} — run `make doc` (build_html.py) first.")

    raw = open(HTML_IN, encoding="utf-8").read()

    # Inject metadata <meta> tags right after the existing <meta charset...> line.
    if 'name="author"' not in raw:
        raw = re.sub(r"(<meta charset=\"utf-8\">\n)", r"\1" + META, raw, count=1)

    html = HTML(string=raw, base_url=DOC)
    html.write_pdf(
        PDF_OUT,
        stylesheets=[CSS(string=PRINT_CSS)],
        pdf_variant="pdf/ua-1",
        uncompressed_pdf=False,
    )

    size_mb = os.path.getsize(PDF_OUT) / 1e6
    print(f"Wrote {PDF_OUT} ({size_mb:.1f} MB) | variant=PDF/UA-1 (tagged)")


if __name__ == "__main__":
    main()
