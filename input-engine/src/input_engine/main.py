from fastapi import FastAPI, HTTPException

from input_engine.detector import detect_content_type
from input_engine.models import ErrorResponse, ExtractionRequest, ExtractionResult
from input_engine.registry import get_handler, list_handlers

# Import handlers to trigger auto-registration
import input_engine.handlers  # noqa: F401

app = FastAPI(
    title="Input Engine",
    description="Content extraction microservice — extract structured data from any content type",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/handlers")
async def handlers():
    return {"handlers": list_handlers()}


@app.post(
    "/extract",
    response_model=ExtractionResult,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def extract(request: ExtractionRequest):
    # Determine content type
    content_type = request.content_type or detect_content_type(request.content)

    # Find handler — try exact match first, then fall back to text
    handler = get_handler(content_type)
    if handler is None:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="no_handler",
                detail=f"No handler registered for content type: {content_type}",
                source_type=content_type,
            ).model_dump(),
        )

    try:
        result = await handler.extract(request.content, request.options)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="extraction_failed",
                detail=str(e),
                source_type=content_type,
            ).model_dump(),
        )
