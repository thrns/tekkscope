from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.models.api_models import ReportLensRequest, ResearchResponse
from app.auth.security import validate_token, validate_token_query
from app.clients.reportlens_client import (
    get_research_report,
    normalize_quality,
    normalize_report_format,
)
from app.streaming import manager
import json
import asyncio

router = APIRouter()

@router.post("/research", response_model=ResearchResponse)
async def research(
    request: ReportLensRequest,
    user: dict = Depends(validate_token)
):
    """
    Generate a structured research report using the ReportLens model.
    """
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    await manager.send_to_client(client_id, {"type": "research_start", "query": request.query})
    result = await get_research_report(request, user_id=client_id, api_key_id=user.get("api_key_id"))
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
    file_format: str = Query("pdf", max_length=20),
    quality: str = Query("standard", max_length=20),
    user: dict = Depends(validate_token_query)
):
    """
    Stream research report generation with quality tiers.
    
    Args:
        query: The research query
        file_format: Output format - 'pdf', 'docx', or 'md' (default: 'pdf')
        quality: Report quality tier (default: 'standard'):
            - "standard": Fast, improved synthesis (7-10 min)
            - "deep": Parallel subsection research (12-18 min)
        user: Authenticated user information
    """
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid token or client ID missing")

    file_format = normalize_report_format(file_format, default="pdf")
    quality = normalize_quality(quality)
    
    # Map quality to boolean for backward compatibility
    is_research_subsection = (quality == "deep")

    queue = await manager.connect(client_id)
    from app.clients.reportlens_client import stream_research_report
    asyncio.create_task(stream_research_report(query, client_id, user_id=client_id, api_key_id=user.get("api_key_id"), file_format=file_format, is_research_subsection=is_research_subsection))
    
    async def cleanup():
        manager.disconnect(client_id, queue)

    return StreamingResponse(event_generator(queue), media_type="text/event-stream", background=cleanup)
