import re
from urllib.parse import urlparse

# URL patterns for specific content types
_YOUTUBE_PATTERNS = re.compile(
    r"(?:youtube\.com|youtu\.be|youtube-nocookie\.com)", re.IGNORECASE
)
_INSTAGRAM_PATTERNS = re.compile(r"(?:instagram\.com|instagr\.am)", re.IGNORECASE)


def detect_content_type(content: str) -> str:
    """Auto-detect content type from input string.

    Returns one of: "youtube", "instagram", "pdf", "url", "markdown", "text"
    """
    stripped = content.strip()

    # Check if it looks like a URL
    if _is_url(stripped):
        return _detect_url_type(stripped)

    # Check for markdown frontmatter
    if stripped.startswith("---"):
        return "markdown"

    return "text"


def _is_url(content: str) -> bool:
    """Check if content looks like a URL."""
    if content.startswith(("http://", "https://", "ftp://")):
        return True
    # Bare domain patterns
    try:
        parsed = urlparse(f"https://{content}")
        return bool(parsed.netloc) and "." in parsed.netloc and " " not in content
    except Exception:
        return False


def _detect_url_type(url: str) -> str:
    """Detect specific content type from a URL."""
    if _YOUTUBE_PATTERNS.search(url):
        return "youtube"

    if _INSTAGRAM_PATTERNS.search(url):
        return "instagram"

    # Check file extension
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith((".md", ".markdown")):
        return "markdown"
    if path.endswith((".eml", ".msg")):
        return "email"

    return "url"
