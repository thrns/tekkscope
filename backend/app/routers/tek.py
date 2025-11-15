import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.auth.security import validate_token_query, validate_token
from app.streaming import manager
from app.clients import tek_client
from app.models.api_models import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)

async def event_generator(queue: asyncio.Queue):
    while True:
        try:
            message = await asyncio.wait_for(queue.get(), timeout=300)
            if message == "[END_OF_STREAM]":
                yield f"data: {json.dumps({'content': '[END_OF_STREAM]'})}\n\n"
                break
            if isinstance(message, dict) and message.get("type") == "response" and message.get("content") == "[END_OF_STREAM]":
                yield f"data: {json.dumps({'content': '[END_OF_STREAM]'})}\n\n"
                break
            yield f"data: {json.dumps(message)}\n\n"
        except asyncio.TimeoutError:
            break
        except asyncio.CancelledError:
            break

@router.post("/tek/chat-completion")
async def tek_chat_completion(request: ChatRequest, user: dict = Depends(validate_token)):
    try:
        client_id = user.get("sub")
        result = await tek_client.get_chat_completion(request, user_id=client_id, api_key_id=user.get("api_key_id"))
        return result
    except Exception:
        logger.exception("Tek chat completion failed")
        raise HTTPException(status_code=500, detail="Chat completion failed") from None

@router.get("/tek/chat-completion/stream")
async def tek_chat_completion_stream(
    query: str = Query(..., min_length=1, max_length=8_000),
    user: dict = Depends(validate_token_query),
):
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid token or client ID missing")

    queue = await manager.connect(client_id)
    asyncio.create_task(tek_client.stream_chat([{"role": "user", "content": query}], client_id, user_id=client_id, api_key_id=user.get("api_key_id")))
    
    async def cleanup():
        manager.disconnect(client_id, queue)

    return StreamingResponse(event_generator(queue), media_type="text/event-stream", background=cleanup)
