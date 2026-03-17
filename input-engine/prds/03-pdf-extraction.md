# PRD: Input Engine — PDF Extraction

**Date:** 2026-03-16
**Status:** Phase 1 Complete (GO)
**Depends on:** 00-base-architecture
**Extraction library:** pymupdf4llm

---

## Goal

Extract clean, structured Markdown from PDF documents. Handles text-heavy PDFs, PDFs with tables, and mixed-layout documents. This covers research papers, ebooks, invoices, receipts, and any other PDF someone might want to process.

---

## Two-Phase Approach

### Phase 1: Standalone Validation Script

**File:** `tests/standalone/test_pdf.py`

**Test against these PDF categories:**
1. Text-heavy document (e.g., a research paper or report)
2. PDF with tables (e.g., financial statement, invoice)
3. Mixed layout — text + images + tables
4. Scanned PDF (image-only, no selectable text) — OCR test
5. Multi-page document (50+ pages)
6. PDF with headers/footers that should be stripped
7. PDF with embedded links
8. Password-protected PDF (should fail gracefully)
9. Corrupted / invalid PDF

**For each test, validate:**
- Text extraction quality — is the Markdown readable?
- Table preservation — are tables rendered as Markdown tables?
- Page count and extraction speed
- Image references captured
- Headers/footers handled (stripped or at least not mixed into body)

**Record results in:** `tests/standalone/results/pdf_results.md`

### Phase 2: Handler Integration

**File:** `src/input_engine/handlers/pdf.py`

```python
class PDFHandler(BaseHandler):
    async def extract(self, content: str, options: ExtractionOptions) -> ExtractionResult:
        # content is either:
        #   - A URL ending in .pdf (download first)
        #   - Base64-encoded PDF data
        # 1. Get PDF bytes (download URL or decode base64)
        # 2. Extract with pymupdf4llm.to_markdown()
        # 3. Extract metadata (title, author, page count, creation date)
        # 4. Map to ExtractionResult

    def can_handle(self, content: str, detected_type: str) -> bool:
        return detected_type == "pdf"
```

**Input handling:**
- URL ending in `.pdf` → download to temp file, extract, cleanup
- Base64 string with `content_type: "pdf"` → decode to bytes, extract
- Raw file path (for local use) → read directly

**Metadata to extract:**
```python
metadata = {
    "page_count": int,
    "author": str | None,         # From PDF metadata
    "creator": str | None,        # PDF creator tool
    "creation_date": str | None,
    "modification_date": str | None,
    "title": str | None,          # From PDF metadata (often unreliable)
    "subject": str | None,
    "word_count": int,
    "has_images": bool,
    "has_tables": bool,
}
```

**Media extraction:**
- Extract embedded images as references (not the binary data)
- If images have alt text or captions, include as description
- Page number where each image appears

---

## Dependencies

```
pymupdf4llm>=0.0.17
pymupdf>=1.24.0
```

---

## Acceptance Criteria

### Phase 1 (Standalone)
- [ ] Script extracts clean Markdown from a text-heavy PDF
- [ ] Tables preserved as Markdown tables
- [ ] Page count and metadata extracted
- [ ] Scanned PDF either OCRs or returns clear "no text found" message
- [ ] Multi-page extraction completes in < 10s for 50-page PDF
- [ ] Results documented with go/no-go decision

### Phase 2 (Integration)
- [ ] `POST /extract` with PDF URL downloads and extracts
- [ ] `POST /extract` with base64 PDF content extracts correctly
- [ ] Large PDFs (100+ pages) don't crash or timeout (< 120s)
- [ ] Password-protected PDFs return clear error
- [ ] Invalid/corrupted PDFs return clear error, not a stack trace
- [ ] Tests pass with fixture PDF files (no network calls)

---

## Known Limitations

- **Scanned PDFs**: pymupdf4llm has OCR support via Tesseract, but quality varies. Complex layouts in scanned docs will be messy. Document, don't solve.
- **Complex layouts**: Multi-column PDFs, magazine-style layouts may produce jumbled text. Known limitation of all PDF extraction.
- **Embedded fonts**: Some PDFs use custom fonts that don't map to Unicode correctly. Rare but possible.
- **Large files**: Very large PDFs (500+ pages) may use significant memory. Consider a page limit option for v2.

---

## Test Fixtures

Include in `tests/fixtures/`:
- `sample_text.pdf` — simple text document (create with reportlab or similar)
- `sample_table.pdf` — document with a table
- `sample_multipage.pdf` — 10+ pages

These should be small, committed to the repo, and deterministic (same extraction output every time).

---

## Test Plan

```bash
# Phase 1: standalone
uv run python tests/standalone/test_pdf.py

# Phase 2: integration
uv run pytest tests/test_pdf_handler.py

# Manual: URL
curl -X POST localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "https://example.com/document.pdf"}'

# Manual: base64
curl -X POST localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "<base64-encoded-pdf>", "content_type": "pdf"}'
```

---

## Out of Scope

- PDF form field extraction
- PDF annotation extraction
- Image-to-text for diagrams/charts (LLM multimodal concern)
- PDF generation/modification
- Page-range selection (extract all pages)

---

## Phase 1 Results

**Library:** pymupdf4llm (pymupdf v1.27.2) | **Pass rate: 3/3 (100%)** | **Decision: GO**

| Category | Status | Pages | Words | Tables | Metadata | Time |
|----------|--------|-------|-------|--------|----------|------|
| Text-heavy document | PASS | 1 | 160 | No | Title, Author | 215ms |
| Document with tables | PASS | 1 | 47 | Yes | Title, Author | 232ms |
| Multi-page (15 pages) | PASS | 15 | 2,626 | No | Title, Author | 818ms |

**Key findings for Phase 2:**
- `pymupdf4llm.to_markdown()` is the right API — returns clean markdown directly
- Use `doc.metadata` for title, author, dates
- Tables render as proper Markdown with `|` separators — works perfectly
- Performance: ~54.5ms/page at scale (100-page PDF ~5.5s, well within 120s timeout)
- Base64 and URL inputs need pre-processing — download/decode to temp file
- OCR requires Tesseract — document as optional dependency for scanned PDFs
- Second table in multi-table PDF was missed — investigate in Phase 2
- `has_tables` detectable by checking for `|` and `---` in output

Full results: `tests/standalone/results/pdf_results.md`

## What Was Done

_(To be filled after implementation)_
