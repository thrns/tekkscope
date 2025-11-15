from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.models.api_models import DeepLensRequest, ResearchResponse
from app.auth.security import validate_token, validate_token_query
from app.clients.deeplens_client import get_detailed_research
from app.streaming import manager
import json
import asyncio

router = APIRouter()

@router.post("/research", response_model=ResearchResponse)
async def research(
    request: DeepLensRequest,
    user: dict = Depends(validate_token)
):
    """
    Perform in-depth, iterative research using the DeepLens model.
    """
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    await manager.send_to_client(client_id, {"type": "research_start", "query": request.query})
    result = await get_detailed_research(request, user_id=client_id, api_key_id=user.get("api_key_id"))
    await manager.send_to_client(client_id, {"type": "research_end", "query": request.query})
    
    return ResearchResponse(result=result)


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
            yield ":\n\n"
            continue
        except asyncio.CancelledError:
            break

@router.get("/research/stream")
async def stream(
    query: str = Query(..., min_length=1, max_length=2_000),
    user: dict = Depends(validate_token_query),
):
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid token or client ID missing")

    queue = await manager.connect(client_id)
    from app.clients.deeplens_client import stream_detailed_research
    asyncio.create_task(stream_detailed_research(query, client_id, user_id=client_id, api_key_id=user.get("api_key_id")))
    
    async def cleanup():
        manager.disconnect(client_id, queue)

    return StreamingResponse(event_generator(queue), media_type="text/event-stream", background=cleanup)
