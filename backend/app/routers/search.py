from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import asyncio
import json
from app.models.api_models import SearchRequest, SearchResponse, SearchResult
from app.clients.search import search_links
from app.clients.scraper import MAX_SCRAPE_SOURCES, stream_search_content
from app.auth.security import validate_token_query
from app.streaming import manager


router = APIRouter()

@router.post("/links", response_model=SearchResponse)
async def search_links_endpoint(
    request: SearchRequest
):
    """
    Perform a search for links using SearXNG.
    """
    raw = await search_links(request.query, request.n_queries, request.num_results, request.enhanced_search)
    results = [{"title": r.get("title",""), "url": r.get("url")} for r in raw]
    search_results = [
        SearchResult(
            title=result.get("title", ""),
            url=result.get("url", ""),
        ) for result in results
    ]
    return SearchResponse(results=search_results)

@router.get("/content")
async def search_content_endpoint(
    query: str = Query(..., min_length=1, max_length=2_000),
    num_results: int = Query(MAX_SCRAPE_SOURCES, ge=1, le=MAX_SCRAPE_SOURCES),
    n_queries: int = Query(3, ge=1, le=10),
    enhanced_search: bool = False,
    user: dict = Depends(validate_token_query)
):
    """
    Perform a search for content using SearXNG and stream the results.
    """
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid token or client ID missing")

    queue = await manager.connect(client_id)
    asyncio.create_task(
        stream_search_content(
            query,
            n_queries,
            num_results,
            enhanced_search,
            client_id,
            api_key_id=user.get("api_key_id"),
        )
    )

    async def event_generator(queue: asyncio.Queue):
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
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

    async def cleanup():
        manager.disconnect(client_id, queue)

    return StreamingResponse(event_generator(queue), media_type="text/event-stream", background=cleanup)

@router.get("/content/stream")
async def search_content_stream(
    query: str = Query(..., min_length=1, max_length=2_000),
    num_results: int = Query(MAX_SCRAPE_SOURCES, ge=1, le=MAX_SCRAPE_SOURCES),
    n_queries: int = Query(3, ge=1, le=10),
    enhanced_search: bool = False,
    user: dict = Depends(validate_token_query)
):
    client_id = user.get("sub")
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid token or client ID missing")

    queue = await manager.connect(client_id)
    asyncio.create_task(
        stream_search_content(
            query,
            n_queries,
            num_results,
            enhanced_search,
            client_id,
            api_key_id=user.get("api_key_id"),
        )
    )

    async def event_generator(queue: asyncio.Queue):
        while True:
            try:
                message = await queue.get()
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.CancelledError:
                break

    async def cleanup():
        manager.disconnect(client_id, queue)

    return StreamingResponse(event_generator(queue), media_type="text/event-stream", background=cleanup)
