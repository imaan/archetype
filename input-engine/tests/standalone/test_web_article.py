"""
Standalone validation: trafilatura for web article extraction.
Run: uv run --with "trafilatura>=1.12.0" python input-engine/tests/standalone/test_web_article.py
No FastAPI dependency required.
"""

import json
import sys
import time
from dataclasses import dataclass, field

import trafilatura


@dataclass
class TestResult:
    url: str
    category: str
    success: bool = False
    title: str | None = None
    author: str | None = None
    date: str | None = None
    body_length: int = 0
    body_preview: str = ""
    images: list[str] = field(default_factory=list)
    has_clean_text: bool = False
    error: str | None = None
    extraction_time_ms: int = 0


TEST_URLS = [
    {
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "category": "Technical documentation",
        "description": "Wikipedia article — well-structured, no ads",
    },
    {
        "url": "https://www.bbc.com/news/science-environment-56837908",
        "category": "News article",
        "description": "BBC News — standard news article structure",
    },
    {
        "url": "https://docs.python.org/3/tutorial/introduction.html",
        "category": "Technical documentation",
        "description": "Python official docs — structured reference",
    },
    {
        "url": "https://paulgraham.com/greatwork.html",
        "category": "Long-form essay",
        "description": "Paul Graham essay — minimal formatting, long text",
    },
    {
        "url": "https://www.craigslist.org/about/",
        "category": "Non-article page",
        "description": "Craigslist about — not a typical article, should degrade gracefully",
    },
    {
        "url": "https://example.com",
        "category": "Minimal page",
        "description": "Example.com — almost no content, tests edge case",
    },
    {
        "url": "https://www.nytimes.com/2024/01/01/technology/ai-2024.html",
        "category": "Paywalled article",
        "description": "NYT — likely paywalled, should extract visible content",
    },
]


def test_extraction(url_info: dict) -> TestResult:
    """Test trafilatura extraction on a single URL."""
    result = TestResult(url=url_info["url"], category=url_info["category"])

    start = time.time()
    try:
        # Fetch the page
        downloaded = trafilatura.fetch_url(url_info["url"])
        if downloaded is None:
            result.error = "fetch_url returned None — page could not be downloaded"
            return result

        # Extract with full metadata
        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_links=True,
            output_format="txt",
            with_metadata=True,
        )

        # Also get metadata separately
        metadata = trafilatura.extract(
            downloaded,
            output_format="xmltei",
            with_metadata=True,
        )

        # Get bare extraction for clean text check
        bare_text = trafilatura.extract(downloaded, include_comments=False)

        if extracted is None and bare_text is None:
            result.error = "extraction returned None — no article content found"
            return result

        text = bare_text or extracted or ""
        result.body_length = len(text)
        result.body_preview = text[:500].replace("\n", " ")
        result.has_clean_text = len(text) > 100

        # Try metadata extraction
        meta = trafilatura.metadata.extract_metadata(downloaded)
        if meta:
            result.title = meta.title
            result.author = meta.author
            result.date = meta.date

        result.success = True

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
    print(f"URL: {result.url}")
    print(f"Time: {result.extraction_time_ms}ms")

    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Title: {result.title or '(not extracted)'}")
        print(f"Author: {result.author or '(not extracted)'}")
        print(f"Date: {result.date or '(not extracted)'}")
        print(f"Body length: {result.body_length} chars")
        print(f"Clean text: {'Yes' if result.has_clean_text else 'No'}")
        print(f"Preview: {result.body_preview[:200]}...")


def main():
    print("=" * 80)
    print("TRAFILATURA STANDALONE VALIDATION")
    print(f"Library version: {trafilatura.__version__}")
    print(f"Testing {len(TEST_URLS)} URLs")
    print("=" * 80)

    results = []
    for i, url_info in enumerate(TEST_URLS):
        print(f"\n>>> Testing {i + 1}/{len(TEST_URLS)}: {url_info['description']}")
        result = test_extraction(url_info)
        results.append(result)
        print_result(result, i)
        # Be polite to servers
        time.sleep(1)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r.success)
    print(f"Passed: {passed}/{len(results)}")
    print()

    print(f"{'Category':<30} {'Status':<8} {'Title':<6} {'Author':<8} {'Date':<6} {'Body':<10} {'Time'}")
    print("-" * 90)
    for r in results:
        status = "PASS" if r.success else "FAIL"
        has_title = "Yes" if r.title else "No"
        has_author = "Yes" if r.author else "No"
        has_date = "Yes" if r.date else "No"
        body = f"{r.body_length:,}" if r.body_length else "0"
        print(f"{r.category:<30} {status:<8} {has_title:<6} {has_author:<8} {has_date:<6} {body:<10} {r.extraction_time_ms}ms")

    # Output JSON for programmatic use
    print("\n\n--- JSON OUTPUT ---")
    json_results = []
    for r in results:
        json_results.append({
            "url": r.url,
            "category": r.category,
            "success": r.success,
            "title": r.title,
            "author": r.author,
            "date": r.date,
            "body_length": r.body_length,
            "has_clean_text": r.has_clean_text,
            "extraction_time_ms": r.extraction_time_ms,
            "error": r.error,
        })
    print(json.dumps(json_results, indent=2))

    return 0 if passed >= len(results) // 2 else 1


if __name__ == "__main__":
    sys.exit(main())
