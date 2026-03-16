import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_handlers_list(client):
    resp = await client.get("/handlers")
    assert resp.status_code == 200
    data = resp.json()
    assert "markdown" in data["handlers"]
    assert "text" in data["handlers"]


@pytest.mark.asyncio
async def test_extract_plain_text(client):
    resp = await client.post("/extract", json={"content": "Hello world"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "text"
    assert data["content"] == "Hello world"
    assert data["extraction_method"] == "passthrough"
    assert data["confidence"] == 1.0


@pytest.mark.asyncio
async def test_extract_markdown_with_frontmatter(client):
    md = "---\ntitle: Test Post\nauthor: Alice\n---\n# Hello\n\nBody text here."
    resp = await client.post("/extract", json={"content": md})
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "markdown"
    assert data["title"] == "Test Post"
    assert data["metadata"]["author"] == "Alice"
    assert "# Hello" in data["content"]
    assert data["extraction_method"] == "frontmatter"


@pytest.mark.asyncio
async def test_extract_with_content_type_override(client):
    resp = await client.post(
        "/extract", json={"content": "some text", "content_type": "text"}
    )
    assert resp.status_code == 200
    assert resp.json()["source_type"] == "text"


@pytest.mark.asyncio
async def test_extract_unhandled_url_falls_back_to_text(client):
    """URLs with no registered handler should fall back to text handler."""
    resp = await client.post(
        "/extract", json={"content": "https://youtube.com/watch?v=abc"}
    )
    assert resp.status_code == 200
    data = resp.json()
    # Falls back to text handler since youtube handler isn't registered
    assert data["source_type"] == "text"


@pytest.mark.asyncio
async def test_extract_options_no_metadata(client):
    resp = await client.post(
        "/extract",
        json={
            "content": "Hello",
            "options": {"include_metadata": False, "include_media_refs": False},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["metadata"] == {}
