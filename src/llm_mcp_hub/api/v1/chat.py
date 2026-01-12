"""Chat API endpoints"""
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from llm_mcp_hub.core.exceptions import LLMHubError
from .dependencies import ChatServiceDep, SessionIdDep
from .schemas import ChatCompletionRequest, ChatCompletionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    chat_service: ChatServiceDep,
    session_id: SessionIdDep,
):
    """
    Chat completion endpoint.

    Supports both streaming and non-streaming responses.
    Use X-Session-ID header to maintain conversation context.
    """
    # Validate messages
    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "Messages cannot be empty"},
        )

    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "At least one user message is required"},
        )

    try:
        if request.stream:
            return StreamingResponse(
                _stream_response(chat_service, request, session_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # Non-streaming response
        result = await chat_service.chat_with_messages(
            messages=[m.model_dump() for m in request.messages],
            provider=request.provider,
            model=request.model,
            session_id=session_id,
            timeout=request.timeout,
        )

        return ChatCompletionResponse(
            response=result["response"],
            session_id=result["session_id"],
            provider=result["provider"],
            model=result["model"],
        )

    except LLMHubError as e:
        logger.error(f"Chat error: {e.code} - {e.message}")
        raise HTTPException(
            status_code=_error_to_status(e.code),
            detail=e.to_dict()["error"],
        )
    except Exception as e:
        logger.exception("Unexpected chat error")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)})


async def _stream_response(chat_service, request: ChatCompletionRequest, session_id: str | None):
    """Generate SSE stream response"""
    try:
        # Extract last user message as prompt
        user_messages = [m for m in request.messages if m.role == "user"]
        if not user_messages:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': 'No user message found'})}\n\n"
            return

        prompt = user_messages[-1].content

        # Extract system prompt
        system_messages = [m for m in request.messages if m.role == "system"]
        system_prompt = system_messages[0].content if system_messages else None

        async for event in chat_service.chat_stream(
            prompt=prompt,
            provider=request.provider,
            model=request.model,
            session_id=session_id,
            system_prompt=system_prompt,
        ):
            if event["type"] == "content":
                data = {
                    "type": "content",
                    "text": event["text"],
                }
                yield f"event: message\ndata: {json.dumps(data)}\n\n"

            elif event["type"] == "done":
                data = {
                    "type": "done",
                    "session_id": event.get("session_id"),
                    "provider": event.get("provider"),
                    "model": event.get("model"),
                }
                yield f"event: done\ndata: {json.dumps(data)}\n\n"

    except LLMHubError as e:
        error_data = {"type": "error", "error": e.message, "code": e.code}
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    except Exception as e:
        error_data = {"type": "error", "error": str(e), "code": "INTERNAL_ERROR"}
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"


def _error_to_status(code: str) -> int:
    """Map error code to HTTP status"""
    status_map = {
        "PROVIDER_MISMATCH": 400,
        "INVALID_MODEL": 400,
        "SESSION_NOT_FOUND": 404,
        "SESSION_EXPIRED": 410,
        "PROVIDER_ERROR": 502,
        "PROVIDER_TIMEOUT": 504,
        "TOKEN_EXPIRED": 401,
    }
    return status_map.get(code, 500)
