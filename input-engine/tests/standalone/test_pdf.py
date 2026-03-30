"""
Standalone validation: pymupdf4llm for PDF extraction.
Run: uv run --with "pymupdf4llm>=0.0.17" --with "pymupdf>=1.24.0" python input-engine/tests/standalone/test_pdf.py

Requires fixtures to be generated first:
  uv run --with "fpdf2>=2.7.0" python input-engine/tests/fixtures/create_pdfs.py
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
import pymupdf4llm

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@dataclass
class TestResult:
    name: str
    category: str
    success: bool = False
    page_count: int = 0
    word_count: int = 0
    markdown_length: int = 0
    markdown_preview: str = ""
    has_tables: bool = False
    title: str | None = None
    author: str | None = None
    creation_date: str | None = None
    extraction_time_ms: int = 0
    error: str | None = None


def extract_metadata(pdf_path: str) -> dict:
    """Extract PDF metadata using pymupdf directly."""
    doc = pymupdf.open(pdf_path)
    meta = doc.metadata
    page_count = len(doc)
    doc.close()
    return {
        "page_count": page_count,
        "title": meta.get("title"),
        "author": meta.get("author"),
        "subject": meta.get("subject"),
        "creator": meta.get("creator"),
        "creation_date": meta.get("creationDate"),
        "modification_date": meta.get("modDate"),
    }


def test_pdf(pdf_path: str, name: str, category: str) -> TestResult:
    """Test pymupdf4llm extraction on a single PDF."""
    result = TestResult(name=name, category=category)

    start = time.time()
    try:
        if not os.path.exists(pdf_path):
            result.error = f"File not found: {pdf_path}"
            return result

        # Extract metadata
        meta = extract_metadata(pdf_path)
        result.page_count = meta["page_count"]
        result.title = meta.get("title")
        result.author = meta.get("author")
        result.creation_date = meta.get("creation_date")

        # Extract markdown
        md_text = pymupdf4llm.to_markdown(pdf_path)

        result.markdown_length = len(md_text)
        result.word_count = len(md_text.split())
        result.markdown_preview = md_text[:800].replace("\n", "\n    ")
        result.has_tables = "|" in md_text and "---" in md_text
        result.success = len(md_text) > 50

    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
    finally:
        result.extraction_time_ms = int((time.time() - start) * 1000)

    return result


def print_result(result: TestResult, index: int):
    """Print a single test result."""
    status = "PASS" if result.success else "FAIL"
    print(f"\n{'='*80}")
    print(f"Test {index + 1}: [{status}] {result.category}")
    print(f"File: {result.name}")
    print(f"Time: {result.extraction_time_ms}ms")

    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Pages: {result.page_count}")
        print(f"Title: {result.title or '(not set)'}")
        print(f"Author: {result.author or '(not set)'}")
        print(f"Words: {result.word_count:,}")
        print(f"Markdown length: {result.markdown_length:,} chars")
        print(f"Has tables: {'Yes' if result.has_tables else 'No'}")
        print(f"Preview:\n    {result.markdown_preview[:500]}...")


def main():
    print("=" * 80)
    print("PYMUPDF4LLM STANDALONE VALIDATION")
    print(f"pymupdf version: {pymupdf.version}")
    print(f"Fixtures directory: {FIXTURES_DIR}")
    print("=" * 80)

    # Check fixtures exist
    required_fixtures = ["sample_text.pdf", "sample_table.pdf", "sample_multipage.pdf"]
    missing = [f for f in required_fixtures if not (FIXTURES_DIR / f).exists()]
    if missing:
        print(f"\nERROR: Missing fixtures: {missing}")
        print("Run first: uv run --with 'fpdf2>=2.7.0' python input-engine/tests/fixtures/create_pdfs.py")
        return 1

    tests = [
        {
            "path": str(FIXTURES_DIR / "sample_text.pdf"),
            "name": "sample_text.pdf",
            "category": "Text-heavy document",
        },
        {
            "path": str(FIXTURES_DIR / "sample_table.pdf"),
            "name": "sample_table.pdf",
            "category": "Document with tables",
        },
        {
            "path": str(FIXTURES_DIR / "sample_multipage.pdf"),
            "name": "sample_multipage.pdf",
            "category": "Multi-page document (15 pages)",
        },
    ]

    results = []
    for i, test in enumerate(tests):
        print(f"\n>>> Testing {i + 1}/{len(tests)}: {test['category']}")
        result = test_pdf(test["path"], test["name"], test["category"])
        results.append(result)
        print_result(result, i)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r.success)
    print(f"Passed: {passed}/{len(results)}")
    print()

    print(f"{'Category':<35} {'Status':<8} {'Pages':<7} {'Words':<8} {'Tables':<8} {'Time'}")
    print("-" * 80)
    for r in results:
        status = "PASS" if r.success else "FAIL"
        tables = "Yes" if r.has_tables else "No"
        print(f"{r.category:<35} {status:<8} {r.page_count:<7} {r.word_count:<8} {tables:<8} {r.extraction_time_ms}ms")

    # Speed benchmark
    print("\n\nSPEED BENCHMARK")
    print("-" * 40)
    for r in results:
        if r.success and r.page_count > 0:
            ms_per_page = r.extraction_time_ms / r.page_count
            print(f"{r.name}: {ms_per_page:.1f}ms/page ({r.page_count} pages in {r.extraction_time_ms}ms)")

    # JSON output
    print("\n\n--- JSON OUTPUT ---")
    json_results = []
    for r in results:
        json_results.append({
            "name": r.name,
            "category": r.category,
            "success": r.success,
            "page_count": r.page_count,
            "word_count": r.word_count,
            "markdown_length": r.markdown_length,
            "has_tables": r.has_tables,
            "title": r.title,
            "author": r.author,
            "extraction_time_ms": r.extraction_time_ms,
            "error": r.error,
        })
    print(json.dumps(json_results, indent=2))

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
