from datetime import datetime, timezone

import frontmatter

from input_engine.handlers.base import BaseHandler
from input_engine.models import ExtractionOptions, ExtractionResult


class TextHandler(BaseHandler):
    """Handles plain text and markdown content (passthrough with optional frontmatter parsing)."""

    def can_handle(self, content: str, detected_type: str) -> bool:
        return detected_type in ("text", "markdown")

    async def extract(
        self, content: str, options: ExtractionOptions
    ) -> ExtractionResult:
        stripped = content.strip()
        is_markdown = stripped.startswith("---")

        if is_markdown:
            return self._extract_markdown(content, options)
        return self._extract_text(content, options)

    def _extract_text(
        self, content: str, options: ExtractionOptions
    ) -> ExtractionResult:
        return ExtractionResult(
            source_type="text",
            content=content,
            metadata={} if not options.include_metadata else {"char_count": len(content)},
            extracted_at=datetime.now(timezone.utc),
            extraction_method="passthrough",
            confidence=1.0,
        )

    def _extract_markdown(
        self, content: str, options: ExtractionOptions
    ) -> ExtractionResult:
        post = frontmatter.loads(content)
        metadata = dict(post.metadata) if options.include_metadata else {}

        return ExtractionResult(
            source_type="markdown",
            title=metadata.get("title"),
            content=post.content,
            metadata=metadata,
            extracted_at=datetime.now(timezone.utc),
            extraction_method="frontmatter",
            confidence=1.0,
        )
