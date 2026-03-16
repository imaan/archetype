"""
Standalone validation: instaloader for Instagram extraction.
Run: uv run --with "instaloader>=4.13.0" python input-engine/tests/standalone/test_instagram.py

WARNING: Instagram aggressively rate-limits. This script adds delays between requests.
Some tests WILL fail — that's expected and documented.
"""

import json
import re
import sys
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import instaloader


@dataclass
class TestResult:
    url: str
    category: str
    shortcode: str = ""
    success: bool = False
    caption: str | None = None
    caption_length: int = 0
    author: str | None = None
    post_type: str | None = None  # photo, carousel, reel/video
    media_count: int = 0
    like_count: int | None = None
    comment_count: int | None = None
    posted_date: str | None = None
    location: str | None = None
    hashtags: list[str] = field(default_factory=list)
    mentioned_users: list[str] = field(default_factory=list)
    is_video: bool = False
    video_url: str | None = None
    thumbnail_url: str | None = None
    error: str | None = None
    error_type: str | None = None  # rate_limit, login_required, not_found, network, other
    extraction_time_ms: int = 0


# Well-known public posts from large accounts (less likely to be deleted)
TEST_POSTS = [
    {
        "url": "https://www.instagram.com/p/C4lHxGWOb1e/",
        "category": "Public photo post",
        "description": "NASA post — large public account, unlikely to be deleted",
    },
    {
        "url": "https://www.instagram.com/p/C5FAKE_INVALID/",
        "category": "Invalid/deleted post",
        "description": "Non-existent shortcode — should fail gracefully",
    },
    {
        "url": "https://www.instagram.com/reel/C4X7OFcOLgE/",
        "category": "Public reel",
        "description": "Reel from public account — video extraction test",
    },
    {
        "url": "https://www.instagram.com/p/C4mVv5_O2nB/",
        "category": "Post with hashtags",
        "description": "Post likely to have hashtags and mentions",
    },
]


def extract_shortcode(url: str) -> str | None:
    """Extract shortcode from Instagram URL."""
    patterns = [
        r"instagram\.com/p/([A-Za-z0-9_-]+)",
        r"instagram\.com/reel/([A-Za-z0-9_-]+)",
        r"instagram\.com/reels/([A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def test_post(loader: instaloader.Instaloader, post_info: dict) -> TestResult:
    """Test extraction of a single Instagram post."""
    result = TestResult(url=post_info["url"], category=post_info["category"])
    result.shortcode = extract_shortcode(post_info["url"]) or ""

    if not result.shortcode:
        result.error = "Could not extract shortcode from URL"
        result.error_type = "parse_error"
        return result

    start = time.time()
    try:
        post = instaloader.Post.from_shortcode(loader.context, result.shortcode)

        # Basic metadata
        result.author = post.owner_username
        result.posted_date = post.date_utc.isoformat() if post.date_utc else None
        result.like_count = post.likes
        result.comment_count = post.comments
        result.is_video = post.is_video

        # Caption and text analysis
        result.caption = post.caption
        if post.caption:
            result.caption_length = len(post.caption)
            # Extract hashtags
            result.hashtags = re.findall(r"#(\w+)", post.caption)
            # Extract mentions
            result.mentioned_users = re.findall(r"@(\w+)", post.caption)

        # Post type
        if post.typename == "GraphSidecar":
            result.post_type = "carousel"
            result.media_count = post.mediacount
        elif post.is_video:
            result.post_type = "reel/video"
            result.video_url = post.video_url
            result.media_count = 1
        else:
            result.post_type = "photo"
            result.media_count = 1

        # Location
        if post.location:
            result.location = post.location.name

        # Thumbnail
        result.thumbnail_url = post.url

        result.success = True

    except instaloader.exceptions.QueryReturnedNotFoundException:
        result.error = "Post not found (404)"
        result.error_type = "not_found"
    except instaloader.exceptions.LoginRequiredException:
        result.error = "Login required to access this post"
        result.error_type = "login_required"
    except instaloader.exceptions.ConnectionException as e:
        error_str = str(e)
        if "429" in error_str or "rate" in error_str.lower():
            result.error = f"Rate limited: {error_str[:200]}"
            result.error_type = "rate_limit"
        else:
            result.error = f"Connection error: {error_str[:200]}"
            result.error_type = "network"
    except Exception as e:
        result.error = f"{type(e).__name__}: {str(e)[:200]}"
        result.error_type = "other"
    finally:
        result.extraction_time_ms = int((time.time() - start) * 1000)

    return result


def print_result(result: TestResult, index: int):
    """Print a single test result."""
    status = "PASS" if result.success else "FAIL"
    print(f"\n{'='*80}")
    print(f"Test {index + 1}: [{status}] {result.category}")
    print(f"URL: {result.url}")
    print(f"Shortcode: {result.shortcode}")
    print(f"Time: {result.extraction_time_ms}ms")

    if result.error:
        print(f"Error type: {result.error_type}")
        print(f"Error: {result.error}")
    else:
        print(f"Author: @{result.author}")
        print(f"Post type: {result.post_type}")
        print(f"Posted: {result.posted_date}")
        print(f"Likes: {result.like_count:,}" if result.like_count is not None else "Likes: hidden")
        print(f"Comments: {result.comment_count:,}" if result.comment_count is not None else "Comments: N/A")
        print(f"Media count: {result.media_count}")
        if result.location:
            print(f"Location: {result.location}")
        if result.is_video:
            print(f"Video URL: {result.video_url[:80]}..." if result.video_url else "Video URL: N/A")
        if result.hashtags:
            print(f"Hashtags: {', '.join('#' + h for h in result.hashtags[:10])}")
        if result.mentioned_users:
            print(f"Mentions: {', '.join('@' + u for u in result.mentioned_users[:10])}")
        if result.caption:
            preview = result.caption[:300].replace("\n", " ")
            print(f"Caption preview: {preview}")


def main():
    print("=" * 80)
    print("INSTAGRAM EXTRACTION STANDALONE VALIDATION")
    print(f"instaloader version: {instaloader.__version__}")
    print("NOTE: Rate limiting is expected. Some tests may fail.")
    print("=" * 80)

    # Create loader with conservative settings
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    results = []
    rate_limited = False

    for i, post_info in enumerate(TEST_POSTS):
        print(f"\n>>> Testing {i + 1}/{len(TEST_POSTS)}: {post_info['description']}")

        if rate_limited:
            print("  (Skipping — already rate limited)")
            result = TestResult(
                url=post_info["url"],
                category=post_info["category"],
                error="Skipped due to prior rate limiting",
                error_type="rate_limit",
            )
            results.append(result)
            continue

        result = test_post(loader, post_info)
        results.append(result)
        print_result(result, i)

        if result.error_type == "rate_limit":
            rate_limited = True
            print("\n  *** Rate limited — skipping remaining real requests ***")

        # Be very conservative with delays
        if i < len(TEST_POSTS) - 1:
            delay = 5
            print(f"\n  Waiting {delay}s before next request...")
            time.sleep(delay)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    rate_limit_count = sum(1 for r in results if r.error_type == "rate_limit")

    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Rate limited: {rate_limit_count}/{len(results)}")
    print()

    print(f"{'Category':<25} {'Status':<8} {'Type':<12} {'Caption':<8} {'Likes':<10} {'Error Type'}")
    print("-" * 80)
    for r in results:
        status = "PASS" if r.success else "FAIL"
        ptype = r.post_type or "-"
        caption = "Yes" if r.caption else "No"
        likes = f"{r.like_count:,}" if r.like_count is not None else "-"
        etype = r.error_type or "-"
        print(f"{r.category:<25} {status:<8} {ptype:<12} {caption:<8} {likes:<10} {etype}")

    # Rate limiting observations
    print("\n\nRATE LIMITING OBSERVATIONS")
    print("-" * 40)
    if rate_limited:
        print("- Rate limiting was triggered during this test run")
        print("- Anonymous access is severely restricted")
        print("- Recommendation: authenticated sessions needed for reliable extraction")
    else:
        print("- No rate limiting observed in this run (may vary)")
        print("- Small sample size — production use will likely hit limits")

    # JSON output
    print("\n\n--- JSON OUTPUT ---")
    json_results = []
    for r in results:
        json_results.append({
            "url": r.url,
            "category": r.category,
            "shortcode": r.shortcode,
            "success": r.success,
            "author": r.author,
            "post_type": r.post_type,
            "caption_length": r.caption_length,
            "like_count": r.like_count,
            "hashtag_count": len(r.hashtags),
            "is_video": r.is_video,
            "location": r.location,
            "error": r.error,
            "error_type": r.error_type,
            "extraction_time_ms": r.extraction_time_ms,
        })
    print(json.dumps(json_results, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
