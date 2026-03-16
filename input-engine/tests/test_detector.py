from input_engine.detector import detect_content_type


def test_plain_text():
    assert detect_content_type("Hello world") == "text"


def test_markdown_frontmatter():
    assert detect_content_type("---\ntitle: Test\n---\n# Hello") == "markdown"


def test_youtube_url():
    assert detect_content_type("https://www.youtube.com/watch?v=abc") == "youtube"


def test_youtube_short_url():
    assert detect_content_type("https://youtu.be/abc123") == "youtube"


def test_instagram_url():
    assert detect_content_type("https://www.instagram.com/p/abc123/") == "instagram"


def test_pdf_url():
    assert detect_content_type("https://example.com/paper.pdf") == "pdf"


def test_generic_url():
    assert detect_content_type("https://example.com/article/hello") == "url"


def test_content_with_spaces_not_url():
    assert detect_content_type("this is a sentence with example.com in it") == "text"


def test_empty_string():
    assert detect_content_type("") == "text"
