# Ring of Fire — build targets
.PHONY: all doc md html pdf export charts charts-static diagrams clean

all: doc charts

doc: html       ## back-compat alias: assemble markdown + self-contained accessible HTML

# --- individual export formats (pick whichever you need) ----------------------
md:             ## export Markdown: build/*.md -> document/Ring-of-Fire-1994.md
	python3 scripts/assemble.py

html: charts-static diagrams  ## export accessible HTML: -> single self-contained document/Ring-of-Fire-1994.html
	python3 scripts/assemble.py
	python3 scripts/build_html.py

pdf: charts-static diagrams   ## export accessible PDF: -> tagged PDF/UA-1 document/Ring-of-Fire-1994.pdf
	python3 scripts/assemble.py
	python3 scripts/build_html.py
	python3 scripts/build_pdf.py

export: pdf     ## build all three deliverables (md + html + pdf) in one pass

charts:         ## generate the standalone interactive charts from the manifest
	cd charts && python3 generate_charts.py --manifest charts.json

charts-static:  ## render static SVG chart fallbacks embedded into the HTML/PDF editions
	python3 charts/generate_static.py

diagrams:       ## render the Mermaid diagrams (Figure 1-1 family tree) to PDF-safe SVG
	python3 charts/render_diagrams.py

clean:
	rm -f charts/out/*.html charts/static/*.svg
	rm -rf work
