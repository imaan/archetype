"""
Standalone validation: Python stdlib email + html-to-markdown for email extraction.
Run: uv run --with "html-to-markdown>=1.0.0" python input-engine/tests/standalone/test_email.py

Requires fixtures to be generated first:
  uv run python input-engine/tests/fixtures/create_emails.py
"""

import email
import email.policy
import json
import os
import sys
import time
from dataclasses import dataclass, field
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

from html_to_markdown import convert as html_to_md

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@dataclass
class TestResult:
    name: str
    category: str
    success: bool = False
    subject: str | None = None
    from_addr: str | None = None
    to_addrs: list[str] = field(default_factory=list)
    cc_addrs: list[str] = field(default_factory=list)
    date: str | None = None
    message_id: str | None = None
    in_reply_to: str | None = None
    body_type: str = ""  # plain, html, multipart
    body_length: int = 0
    body_preview: str = ""
    markdown_body: str = ""
    attachments: list[dict] = field(default_factory=list)
    has_forwarded_content: bool = False
    has_quoted_content: bool = False
    error: str | None = None
    parse_time_ms: int = 0


def parse_email_file(eml_path: str, name: str, category: str) -> TestResult:
    """Parse an .eml file and extract all components."""
    result = TestResult(name=name, category=category)

    start = time.time()
    try:
        raw = Path(eml_path).read_text(encoding="utf-8")
        msg = email.message_from_string(raw, policy=email.policy.default)

        # Headers
        result.subject = msg["subject"]
        result.from_addr = msg["from"]
        result.message_id = msg["message-id"]
        result.in_reply_to = msg.get("in-reply-to")

        # Parse To and CC
        if msg["to"]:
            result.to_addrs = [addr.strip() for addr in msg["to"].split(",")]
        if msg["cc"]:
            result.cc_addrs = [addr.strip() for addr in msg["cc"].split(",")]

        # Parse date
        try:
            if msg["date"]:
                dt = parsedate_to_datetime(msg["date"])
                result.date = dt.isoformat()
        except Exception:
            result.date = msg.get("date", "(unparseable)")

        # Extract body
        body_text = ""
        html_body = ""

        if msg.is_multipart():
            result.body_type = "multipart"
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in disposition:
                    # Attachment
                    filename = part.get_filename() or "unnamed"
                    size = len(part.get_payload(decode=True) or b"")
                    result.attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": size,
                    })
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
                if content_type == "text/html":
                    result.body_type = "html"
                    html_body = text
                else:
                    result.body_type = "plain"
                    body_text = text

        # Convert HTML to Markdown if we have HTML but no plain text
        if html_body and not body_text:
            try:
                body_text = html_to_md(html_body)
                result.markdown_body = body_text[:500]
            except Exception as e:
                body_text = f"[HTML conversion failed: {e}]"
        elif html_body and body_text:
            # We have both — also convert HTML for comparison
            try:
                result.markdown_body = html_to_md(html_body)[:500]
            except Exception:
                pass

        result.body_length = len(body_text)
        result.body_preview = body_text[:500]

        # Detect forwarded/quoted content
        result.has_forwarded_content = any(
            marker in body_text
            for marker in ["---------- Forwarded message", "Begin forwarded message", "-------- Original Message"]
        )
        result.has_quoted_content = body_text.count("\n>") >= 2

        result.success = True

    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
    finally:
        result.parse_time_ms = int((time.time() - start) * 1000)

    return result


def print_result(result: TestResult, index: int):
    """Print a single test result."""
    status = "PASS" if result.success else "FAIL"
    print(f"\n{'='*80}")
    print(f"Test {index + 1}: [{status}] {result.category}")
    print(f"File: {result.name}")
    print(f"Time: {result.parse_time_ms}ms")

    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Subject: {result.subject}")
        print(f"From: {result.from_addr}")
        print(f"To: {', '.join(result.to_addrs)}")
        if result.cc_addrs:
            print(f"CC: {', '.join(result.cc_addrs)}")
        print(f"Date: {result.date}")
        print(f"Body type: {result.body_type}")
        print(f"Body length: {result.body_length:,} chars")
        if result.attachments:
            print(f"Attachments ({len(result.attachments)}):")
            for att in result.attachments:
                print(f"  - {att['filename']} ({att['content_type']}, {att['size_bytes']} bytes)")
        if result.has_forwarded_content:
            print("Forwarded content: DETECTED")
        if result.has_quoted_content:
            print("Quoted replies: DETECTED")
        if result.in_reply_to:
            print(f"In-Reply-To: {result.in_reply_to}")
        print(f"Preview:\n  {result.body_preview[:300]}")
        if result.markdown_body:
            print(f"\nMarkdown conversion preview:\n  {result.markdown_body[:300]}")


def main():
    print("=" * 80)
    print("EMAIL EXTRACTION STANDALONE VALIDATION")
    print(f"Fixtures directory: {FIXTURES_DIR}")
    print("=" * 80)

    fixture_tests = [
        ("sample_plain.eml", "Plain text email"),
        ("sample_html.eml", "HTML newsletter email"),
        ("sample_attachment.eml", "Email with attachments"),
        ("sample_forwarded.eml", "Forwarded email"),
        ("sample_reply_chain.eml", "Reply chain with quotes"),
        ("sample_unicode.eml", "Unicode + emoji email"),
    ]

    # Check fixtures exist
    missing = [f for f, _ in fixture_tests if not (FIXTURES_DIR / f).exists()]
    if missing:
        print(f"\nERROR: Missing fixtures: {missing}")
        print("Run first: uv run python input-engine/tests/fixtures/create_emails.py")
        return 1

    results = []
    for i, (filename, category) in enumerate(fixture_tests):
        print(f"\n>>> Testing {i + 1}/{len(fixture_tests)}: {category}")
        result = parse_email_file(str(FIXTURES_DIR / filename), filename, category)
        results.append(result)
        print_result(result, i)

    # Also test a malformed email
    print(f"\n>>> Testing {len(fixture_tests) + 1}/{len(fixture_tests) + 1}: Malformed email (inline)")
    malformed_result = parse_email_file_from_string(
        "This is not a valid email at all.\nJust random text.\n",
        "inline_malformed",
        "Malformed / no headers",
    )
    results.append(malformed_result)
    print_result(malformed_result, len(fixture_tests))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r.success)
    print(f"Passed: {passed}/{len(results)}")
    print()

    print(f"{'Category':<30} {'Status':<8} {'Subject':<6} {'From':<6} {'Body':<8} {'Attach':<8} {'Time'}")
    print("-" * 85)
    for r in results:
        status = "PASS" if r.success else "FAIL"
        has_subj = "Yes" if r.subject else "No"
        has_from = "Yes" if r.from_addr else "No"
        body = f"{r.body_length:,}" if r.body_length else "0"
        attach = str(len(r.attachments)) if r.attachments else "-"
        print(f"{r.category:<30} {status:<8} {has_subj:<6} {has_from:<6} {body:<8} {attach:<8} {r.parse_time_ms}ms")

    # JSON output
    print("\n\n--- JSON OUTPUT ---")
    json_results = []
    for r in results:
        json_results.append({
            "name": r.name,
            "category": r.category,
            "success": r.success,
            "subject": r.subject,
            "from": r.from_addr,
            "body_type": r.body_type,
            "body_length": r.body_length,
            "attachment_count": len(r.attachments),
            "has_forwarded": r.has_forwarded_content,
            "has_quoted": r.has_quoted_content,
            "parse_time_ms": r.parse_time_ms,
            "error": r.error,
        })
    print(json.dumps(json_results, indent=2))

    return 0


def parse_email_file_from_string(raw: str, name: str, category: str) -> TestResult:
    """Parse email from a raw string (for inline test cases)."""
    result = TestResult(name=name, category=category)

    start = time.time()
    try:
        msg = email.message_from_string(raw, policy=email.policy.default)
        result.subject = msg["subject"]
        result.from_addr = msg["from"]

        payload = msg.get_payload(decode=True)
        if payload:
            result.body_preview = payload.decode("utf-8", errors="replace")[:500]
            result.body_length = len(result.body_preview)
        elif isinstance(msg.get_payload(), str):
            result.body_preview = msg.get_payload()[:500]
            result.body_length = len(result.body_preview)

        result.body_type = "plain"
        result.success = True
    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
    finally:
        result.parse_time_ms = int((time.time() - start) * 1000)

    return result


if __name__ == "__main__":
    sys.exit(main())
