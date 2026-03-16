from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from input_engine.handlers.base import BaseHandler

_registry: dict[str, BaseHandler] = {}


def register(content_type: str, handler: BaseHandler) -> None:
    """Register a handler for a content type."""
    _registry[content_type] = handler


def get_handler(content_type: str) -> BaseHandler | None:
    """Look up a handler by content type, falling back to text handler."""
    if content_type in _registry:
        return _registry[content_type]
    return _registry.get("text")


def list_handlers() -> list[str]:
    """Return list of registered content types."""
    return sorted(_registry.keys())
