"""
Generate test fixture PDFs for Phase 1 validation.
Run: uv run --with "fpdf2>=2.7.0" python input-engine/tests/fixtures/create_pdfs.py
"""

import os
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

FIXTURES_DIR = Path(__file__).parent


def create_text_pdf():
    """Create a simple multi-paragraph text document."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Sample Text Document", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)

    paragraphs = [
        "This is a sample text document created for testing PDF extraction with pymupdf4llm. "
        "The purpose of this document is to validate that text extraction works correctly for "
        "standard text-heavy documents with multiple paragraphs and sections.",

        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",

        "Python is a high-level, general-purpose programming language. Its design philosophy "
        "emphasizes code readability with the use of significant indentation. Python is "
        "dynamically typed and garbage-collected. It supports multiple programming paradigms, "
        "including structured, object-oriented and functional programming.",
    ]

    for para in paragraphs:
        pdf.multi_cell(0, 6, para)
        pdf.ln(4)

    # Add a second section
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Section 2: Technical Details", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 11)
    technical_text = (
        "The extraction engine processes documents through multiple stages. First, the raw "
        "content is fetched from the source. Then, the appropriate handler is selected based "
        "on content type detection. Finally, the handler extracts structured data including "
        "the main text content, metadata, and any media references."
    )
    pdf.multi_cell(0, 6, technical_text)

    # Set metadata
    pdf.set_title("Sample Text Document")
    pdf.set_author("Test Author")
    pdf.set_subject("PDF Extraction Testing")
    pdf.set_creation_date(datetime.now())

    output_path = FIXTURES_DIR / "sample_text.pdf"
    pdf.output(str(output_path))
    print(f"Created: {output_path} ({os.path.getsize(output_path)} bytes)")


def create_table_pdf():
    """Create a document with tables."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Sales Report Q1 2026", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, "This report contains quarterly sales data organized in tabular format.")
    pdf.ln(5)

    # Table header
    pdf.set_font("Helvetica", "B", 10)
    col_widths = [50, 35, 35, 35, 35]
    headers = ["Product", "January", "February", "March", "Total"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, align="C")
    pdf.ln()

    # Table data
    pdf.set_font("Helvetica", "", 10)
    data = [
        ["Widget Alpha", "$12,500", "$14,200", "$13,800", "$40,500"],
        ["Widget Beta", "$8,300", "$9,100", "$11,200", "$28,600"],
        ["Widget Gamma", "$22,100", "$19,800", "$24,500", "$66,400"],
        ["Service Plan A", "$5,000", "$5,000", "$5,000", "$15,000"],
        ["Service Plan B", "$3,200", "$3,200", "$3,200", "$9,600"],
    ]
    for row in data:
        for w, cell in zip(col_widths, row):
            align = "L" if row.index(cell) == 0 else "R"
            pdf.cell(w, 7, cell, border=1, align=align)
        pdf.ln()

    # Totals row
    pdf.set_font("Helvetica", "B", 10)
    totals = ["TOTAL", "$51,100", "$51,300", "$57,700", "$160,100"]
    for w, cell in zip(col_widths, totals):
        align = "L" if totals.index(cell) == 0 else "R"
        pdf.cell(w, 8, cell, border=1, align=align)
    pdf.ln(15)

    # Second table
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Regional Breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    col_widths2 = [60, 40, 40, 50]
    headers2 = ["Region", "Revenue", "Growth %", "Top Product"]
    for w, h in zip(col_widths2, headers2):
        pdf.cell(w, 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    regions = [
        ["North America", "$85,000", "+12%", "Widget Gamma"],
        ["Europe", "$42,000", "+8%", "Widget Alpha"],
        ["Asia Pacific", "$33,100", "+22%", "Widget Beta"],
    ]
    for row in regions:
        for w, cell in zip(col_widths2, row):
            pdf.cell(w, 7, cell, border=1)
        pdf.ln()

    pdf.set_title("Sales Report Q1 2026")
    pdf.set_author("Finance Department")
    pdf.set_creation_date(datetime.now())

    output_path = FIXTURES_DIR / "sample_table.pdf"
    pdf.output(str(output_path))
    print(f"Created: {output_path} ({os.path.getsize(output_path)} bytes)")


def create_multipage_pdf():
    """Create a 15-page document."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_title("Multi-Page Test Document")
    pdf.set_author("Test Generator")
    pdf.set_creation_date(datetime.now())

    topics = [
        ("Introduction", "This document tests multi-page PDF extraction. It contains 15 pages of varied content to validate that the extraction engine handles page boundaries correctly."),
        ("Chapter 1: Background", "The field of document extraction has evolved significantly over the past decade. Early approaches relied on simple text extraction, while modern systems use sophisticated layout analysis."),
        ("Chapter 2: Methodology", "Our approach uses a plugin-based architecture where each content type has a dedicated handler. The handler implements a standard interface with can_handle() and extract() methods."),
        ("Chapter 3: Implementation", "The implementation uses Python with FastAPI for the web framework. Each handler is registered in a central registry and selected based on content type detection."),
        ("Chapter 4: Results", "Testing across multiple document types shows that pymupdf4llm provides excellent extraction quality for text-heavy documents and reasonable table preservation."),
        ("Chapter 5: Analysis", "The analysis reveals that extraction quality depends heavily on the source document structure. Well-formatted documents yield near-perfect results."),
        ("Chapter 6: Discussion", "Several factors influence extraction quality: font embedding, layout complexity, image density, and the use of headers and footers."),
        ("Chapter 7: Related Work", "Related tools include pdfminer, pdfplumber, camelot, and tabula. Each has strengths in specific areas but pymupdf4llm offers the best general-purpose extraction."),
        ("Chapter 8: Future Work", "Future improvements could include better table detection, image captioning with multimodal models, and support for complex multi-column layouts."),
        ("Chapter 9: Limitations", "Current limitations include poor handling of scanned documents without OCR, difficulty with complex mathematical notation, and challenges with multi-language documents."),
        ("Chapter 10: Conclusion", "In conclusion, pymupdf4llm provides a solid foundation for PDF extraction in the input engine. Its combination of speed, quality, and markdown output format aligns well with our requirements."),
        ("Appendix A: Configuration", "The PDF handler accepts several configuration options: page_range, include_images, table_detection_mode, and strip_headers_footers."),
        ("Appendix B: Benchmarks", "Extraction speed benchmarks across document sizes: 1 page = 50ms, 10 pages = 200ms, 50 pages = 800ms, 100 pages = 1.5s, 500 pages = 7s."),
        ("Appendix C: Error Codes", "Error codes returned by the PDF handler: PDF_ENCRYPTED, PDF_CORRUPTED, PDF_EMPTY, PDF_TOO_LARGE, PDF_TIMEOUT, PDF_UNSUPPORTED_VERSION."),
        ("References", "1. PyMuPDF Documentation. 2. PDF Reference Manual, Adobe Systems. 3. Extracting Structured Data from PDFs, ACL 2023. 4. Layout Analysis for Document Understanding, CVPR 2024."),
    ]

    for title, intro in topics:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, intro)
        pdf.ln(4)

        # Add filler content to make pages fuller
        filler = (
            "This section contains additional detail to ensure the page has sufficient "
            "content for extraction testing. The extraction engine should handle page "
            "boundaries seamlessly, combining content from multiple pages into a single "
            "coherent document. Headers and footers should ideally be stripped or at least "
            "not mixed into the main body text. "
        ) * 3
        pdf.multi_cell(0, 6, filler)

    output_path = FIXTURES_DIR / "sample_multipage.pdf"
    pdf.output(str(output_path))
    print(f"Created: {output_path} ({os.path.getsize(output_path)} bytes, 15 pages)")


if __name__ == "__main__":
    print("Generating PDF test fixtures...")
    print(f"Output directory: {FIXTURES_DIR}")
    print()
    create_text_pdf()
    create_table_pdf()
    create_multipage_pdf()
    print("\nDone! All fixtures created.")
