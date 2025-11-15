import os
from dotenv import load_dotenv
from fastapi import HTTPException
from app.research_lib.api.research_functions import quick_summary
from app.research_lib.api.settings_utils import create_settings_snapshot as ldr_create_settings_snapshot
from app.research_lib.utilities.markdown_formatter import format_research_output
from app.research_lib.utilities.prompt_enhancer import enhance_lens_prompt
from app.research_lib.utilities.query_preprocessor import preprocess_query_for_research
from app.research_lib.config.llm_config import get_llm
from app.research_lib.config.provider_router import provider_overrides_from_env
from app.clients.search import search_searxng
from app.utils.response_utils import to_serializable
from app.models.api_models import LensRequest, ResearchResponse
from app.streaming import manager
import asyncio
from app.clients.supabase_client import supabase, decrement_credits
from app.config.credit_rates import compute_credits_used
from app.utils.rate_limiter import check_rate_limit
from loguru import logger
import uuid

load_dotenv()


def create_settings_snapshot(request: LensRequest) -> dict:
    max_tokens = int(os.getenv("TEKK_LLM_MAX_TOKENS", "16000"))

    overrides = provider_overrides_from_env(
        max_tokens=max_tokens,
        temperature=0.7,
        search_tool="searxng",
        search_instance_url=os.getenv(
            "TEKK_SEARXNG_URL", "https://search.tekkscope.com"
        ),
    )
    return ldr_create_settings_snapshot(overrides=overrides)


async def get_quick_summary(request: LensRequest, user_id: str, api_key_id: str | None = None) -> dict:
    if user_id and api_key_id:
        await check_rate_limit(api_key_id, user_id)

    settings_snapshot = create_settings_snapshot(request)
    
    # Preprocess query: decompose if needed, enhance for synthesis
    try:
        llm = get_llm(settings_snapshot=settings_snapshot)
        preprocessed = preprocess_query_for_research(
            raw_query=request.query,
            llm=llm,
            mode="lens",
            max_sub_queries=5
        )
    except Exception as e:
        logger.warning(f"Failed to preprocess query (LLM error): {e}, using query as-is")
        # Fallback: use original query without decomposition
        preprocessed = {
            "search_queries": [request.query],
            "synthesis_prompt": enhance_lens_prompt(request.query),
            "original_query": request.query,
            "was_decomposed": False
        }
    
    # Use decomposed queries for search, enhanced prompt for synthesis
    result = quick_summary(
        query=preprocessed["synthesis_prompt"],  # Use enhanced prompt for synthesis
        search_queries=preprocessed["search_queries"],  # Use decomposed queries for search
        search_tool=None,  # Let settings_snapshot determine the search tool
        max_results=10,
        settings_snapshot=settings_snapshot,
        programmatic_mode=True,
    )
    serial = to_serializable(result)
    try:
        summary_text = serial.get("summary") or ""
        total_tokens = max(1, round(len(summary_text) / 4))
        input_tokens = max(1, round(total_tokens * 0.7))
        output_tokens = max(1, round(total_tokens * 0.3))
        # Ensure they sum to total_tokens
        if input_tokens + output_tokens != total_tokens:
            output_tokens = total_tokens - input_tokens
        if input_tokens + output_tokens != total_tokens:
            output_tokens = total_tokens - input_tokens
        credits_used = compute_credits_used(input_tokens, output_tokens, "TEKKSCOPE", "lens")
        provider = "GEMINI"
        model = os.getenv("TEKK_LLM_MODEL", "gemini-2.0-flash")
        research_id = str(uuid.uuid4())
        supabase.table("research_outputs").insert({
            "user_id": user_id,
            "research_id": research_id,
            "mode": "lens",
            "query": request.query,
            "summary": summary_text,
            "formatted_findings": serial.get("formatted_findings"),
            "findings": serial.get("findings"),
            "sources": serial.get("sources"),
            "model": model,
            "provider": provider,
        }).execute()
        supabase.table("usage").insert({
            "user_id": user_id,
            "service_used": "lens",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "credits_used": credits_used,
            "research_id": research_id,
            "api_token_id": api_key_id,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()+"Z",
        }).execute()
    except Exception:
        pass
    return serial


async def stream_quick_summary(query: str, client_id: str, user_id: str, api_key_id: str | None = None) -> None:
    # Check rate limit and send error to client if exceeded
    if client_id and api_key_id:
        try:
            await check_rate_limit(api_key_id, user_id)
        except HTTPException as e:
            await manager.send_to_client(client_id, {"type": "error", "content": e.detail})
            await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
            return

    settings_snapshot = create_settings_snapshot(LensRequest(query=query))

    try:
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "start", "iterations": 0, "query": query}})
        
        # Preprocess query: decompose if needed, enhance for synthesis
        try:
            llm = get_llm(settings_snapshot=settings_snapshot)
            preprocessed = preprocess_query_for_research(
                raw_query=query,
                llm=llm,
                mode="lens",
                max_sub_queries=5
            )
        except Exception as e:
            logger.warning(f"Failed to preprocess query (LLM error): {e}, using query as-is")
            # Fallback: use original query without decomposition
            preprocessed = {
                "search_queries": [query],
                "synthesis_prompt": enhance_lens_prompt(query),
                "original_query": query,
                "was_decomposed": False
            }
        
        # Use first search query for preview (or original if not decomposed)
        preview_query = preprocessed["search_queries"][0] if preprocessed["search_queries"] else query
        urls_preview = await search_searxng(preview_query, 6)
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "urls_preview", "iterations": 0, "query": query, "urls": [u.get("url") for u in urls_preview[:6]]}})
        
        if preprocessed["was_decomposed"]:
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "query_decomposition", "message": f"Decomposed query into {len(preprocessed['search_queries'])} search queries", "iterations": 0}})
        
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "calling_quick_summary", "iterations": 0, "query": query}})
        try:
            loop = asyncio.get_running_loop()
            def on_progress(message: str, progress: int, metadata: dict):
                phase = metadata.get("phase", "progress")
                stage = phase
                if phase in {"analysis", "search_complete", "final_filtering", "filtering_complete"}:
                    stage = "search"
                elif phase in {"synthesis", "finalizing"}:
                    stage = "summarizing"
                links_preview = metadata.get("links_preview") or []
                url = None
                if isinstance(links_preview, list) and links_preview:
                    first = links_preview[0]
                    url = first.get("url") if isinstance(first, dict) else None
                narrative = metadata.get("question") or message
                payload = {"type": "thinking", "content": {"phase": phase, "stage": stage, "message": message, "progress": progress, "url": url, "narrative": narrative, **metadata}}
                try:
                    import asyncio as _asyncio
                    _asyncio.run_coroutine_threadsafe(manager.send_to_client(client_id, payload), loop)
                except Exception:
                    pass
            result = await asyncio.to_thread(
                quick_summary,
                query=preprocessed["synthesis_prompt"],  # Use enhanced prompt for synthesis
                search_queries=preprocessed["search_queries"],  # Use decomposed queries for search
                search_tool=None,  # Let settings_snapshot determine the search tool
                max_results=10,
                settings_snapshot=settings_snapshot,
                programmatic_mode=True,
                progress_callback=on_progress,
            )
        except Exception as e:
            await manager.send_to_client(client_id, {"type": "error", "content": f"{type(e).__name__}: {str(e)}"})
            await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
            await manager.send_to_client(client_id, "[END_OF_STREAM]")
            return
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "summarizing", "iterations": 1, "query": query}})
        serial = to_serializable(result)
        try:
            summary_text = serial.get("summary") or ""
            # Format markdown output
            summary_text = format_research_output(summary_text)
            serial["summary"] = summary_text
            
            total_tokens = max(1, round(len(summary_text) / 4))
            input_tokens = max(1, round(total_tokens * 0.7))
            output_tokens = max(1, round(total_tokens * 0.3))
            # Ensure they sum to total_tokens
            if input_tokens + output_tokens != total_tokens:
                output_tokens = total_tokens - input_tokens
            if input_tokens + output_tokens != total_tokens:
                output_tokens = total_tokens - input_tokens
            credits_used = compute_credits_used(input_tokens, output_tokens, "TEKKSCOPE", "lens")
            provider = "GEMINI"
            model = os.getenv("TEKK_LLM_MODEL", "gemini-2.0-flash")
            research_id = str(uuid.uuid4())
            supabase.table("research_outputs").insert({
                "user_id": user_id,
                "research_id": research_id,
                "mode": "lens",
                "query": query,
                "summary": summary_text,
                "formatted_findings": serial.get("formatted_findings"),
                "findings": serial.get("findings"),
                "sources": serial.get("sources"),
                "model": model,
                "provider": provider,
            }).execute()
            supabase.table("usage").insert({
                "user_id": user_id,
                "service_used": "lens",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "credits_used": credits_used,
                "research_id": research_id,
                "api_token_id": api_key_id,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat()+"Z",
            }).execute()
            try:
                decrement_credits(user_id, credits_used)
            except Exception:
                pass
        except Exception:
            pass
        try:
            citations = serial.get("sources")
            if citations:
                await manager.send_to_client(client_id, {"type": "response", "content": {"citations": citations}})
        except Exception:
            pass
        def pick_text(d):
            if isinstance(d, dict):
                for k in ["summary","answer","report","content","text"]:
                    v = d.get(k)
                    if isinstance(v, str) and v.strip():
                        return v
                for v in d.values():
                    if isinstance(v, dict):
                        t = pick_text(v)
                        if t:
                            return t
            return ""
        text = pick_text(serial) or str(serial)
        chunk_size = 60
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            if chunk:
                await manager.send_to_client(client_id, {"type": "response", "content": chunk})
                await asyncio.sleep(0)
        await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
        await manager.send_to_client(client_id, "[END_OF_STREAM]")
    except Exception as e:
        await manager.send_to_client(client_id, {"type": "error", "content": f"{type(e).__name__}: {str(e)}"})
        await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
        await manager.send_to_client(client_id, "[END_OF_STREAM]")
        raise
