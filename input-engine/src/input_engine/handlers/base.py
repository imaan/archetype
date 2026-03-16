from abc import ABC, abstractmethod

from input_engine.models import ExtractionOptions, ExtractionResult


class BaseHandler(ABC):
    @abstractmethod
    async def extract(
        self, content: str, options: ExtractionOptions
    ) -> ExtractionResult:
        """Extract structured data from content."""
        ...

    @abstractmethod
    def can_handle(self, content: str, detected_type: str) -> bool:
        """Return True if this handler can process the given content."""
        ...
