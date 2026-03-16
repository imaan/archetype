import pytest

from input_engine.handlers.text import TextHandler
from input_engine.models import ExtractionOptions


@pytest.fixture
def handler():
    return TextHandler()


@pytest.fixture
def options():
    return ExtractionOptions()


def test_can_handle_text(handler):
    assert handler.can_handle("hello", "text") is True


def test_can_handle_markdown(handler):
    assert handler.can_handle("# title", "markdown") is True


def test_cannot_handle_youtube(handler):
    assert handler.can_handle("https://youtube.com", "youtube") is False


@pytest.mark.asyncio
async def test_extract_plain_text(handler, options):
    result = await handler.extract("Hello world", options)
    assert result.source_type == "text"
    assert result.content == "Hello world"
    assert result.extraction_method == "passthrough"
    assert result.confidence == 1.0
    assert result.metadata["char_count"] == 11


@pytest.mark.asyncio
async def test_extract_plain_text_no_metadata(handler):
    options = ExtractionOptions(include_metadata=False)
    result = await handler.extract("Hello", options)
    assert result.metadata == {}


@pytest.mark.asyncio
async def test_extract_markdown(handler, options):
    md = "---\ntitle: My Post\ntags:\n  - python\n  - api\n---\n# Content\n\nBody here."
    result = await handler.extract(md, options)
    assert result.source_type == "markdown"
    assert result.title == "My Post"
    assert result.metadata["title"] == "My Post"
    assert result.metadata["tags"] == ["python", "api"]
    assert "# Content" in result.content
    assert result.extraction_method == "frontmatter"


@pytest.mark.asyncio
async def test_extract_markdown_no_frontmatter_values(handler, options):
    md = "---\n---\nJust content"
    result = await handler.extract(md, options)
    assert result.source_type == "markdown"
    assert result.content == "Just content"
    assert result.metadata == {}
