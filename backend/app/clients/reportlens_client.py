import os
import logging
import re
from dotenv import load_dotenv
from fastapi import HTTPException
from app.research_lib.api.research_functions import generate_report
from app.research_lib.api.settings_utils import create_settings_snapshot as ldr_create_settings_snapshot
from app.research_lib.utilities.markdown_formatter import format_research_output
from app.research_lib.utilities.prompt_enhancer import enhance_reportlens_prompt
from app.research_lib.utilities.query_preprocessor import preprocess_query_for_research
from app.research_lib.config.llm_config import get_llm
from app.research_lib.config.provider_router import (
    normalize_provider_name,
    provider_model,
    provider_overrides_from_env,
)
from app.utils.response_utils import to_serializable
from app.utils.report_generator import generate_report_file
from app.clients.search import search_searxng
from app.models.api_models import ReportLensRequest, ResearchResponse
from app.streaming import manager
import asyncio
from app.clients.supabase_client import supabase, decrement_credits
from app.config.credit_rates import compute_credits_used
from app.utils.rate_limiter import check_rate_limit
from loguru import logger
import uuid

load_dotenv()

SUPPORTED_REPORT_FORMATS = {"pdf", "docx", "md"}
REPORT_MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}
QUALITY_PRESETS = {
    "standard": {
        "max_results": 8,
        "iterations": 2,
        "is_research_subsection": False,
    },
    "deep": {
        "max_results": 12,
        "iterations": 2,
        "is_research_subsection": True,
    },
}


def normalize_report_format(value: str | None, default: str = "md") -> str:
    normalized = (value or default).strip().lower()
    if normalized == "markdown":
        normalized = "md"
    return normalized if normalized in SUPPORTED_REPORT_FORMATS else default


def normalize_quality(value: str | None, default: str = "standard") -> str:
    normalized = (value or default).strip().lower()
    return normalized if normalized in QUALITY_PRESETS else default


def _safe_report_filename(query: str, research_id: str, file_extension: str) -> str:
    safe_filename = re.sub(r"[^\w\s-]", "", query).strip().lower()
    safe_filename = re.sub(r"[-\s]+", "-", safe_filename)
    return f"{safe_filename or 'report'}-{research_id[:8]}.{file_extension}"


def _safe_storage_prefix(client_id: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9_-]", "-", str(client_id)).strip("-")
    return prefix or "anonymous"


async def _create_report_download(
    content: str,
    query: str,
    client_id: str,
    file_format: str,
    research_id: str,
) -> dict:
    """Render and upload a report without blocking the async request loop."""

    file_extension = normalize_report_format(file_format)
    filename = _safe_report_filename(query, research_id, file_extension)
    path = f"{_safe_storage_prefix(client_id)}/{filename}"
    file_bytes = await asyncio.to_thread(
        generate_report_file,
        content,
        file_format=file_extension,
        title=query[:100],
    )
    content_type = REPORT_MIME_TYPES[file_extension]

    def upload() -> str:
        storage = supabase.storage.from_("reports")
        storage.upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        return storage.get_public_url(path)

    public_url = await asyncio.to_thread(upload)
    if not public_url:
        raise RuntimeError("Report storage did not return a download URL")
    return {
        "download_url": public_url,
        "file_format": file_extension,
        "filename": filename,
        "research_id": research_id,
    }


def extract_executive_summary(content: str) -> str:
    """
    Extract executive summary from report content.
    
    Strategy:
    1. Look for "Executive Summary" or "Summary" section in markdown
    2. If not found, extract introduction/first section (content before first major heading)
    3. If neither, use first 800-1000 characters as fallback
    
    Args:
        content: Full report content in markdown format
        
    Returns:
        Formatted executive summary text
    """
    if not content:
        return ""
    
    # Try to find Executive Summary or Summary section
    # Look for headings like: # Executive Summary, ## Executive Summary, # Summary, etc.
    summary_patterns = [
        r'(?:^|\n)#+\s*(?:Executive\s+)?Summary[^\n]*\n\n(.*?)(?=\n#+\s|$)',
        r'(?:^|\n)#+\s*Executive\s+Summary[^\n]*\n\n(.*?)(?=\n#+\s|$)',
    ]
    
    for pattern in summary_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            summary = match.group(1).strip()
            if summary and len(summary) > 50:  # Ensure it's substantial
                # Clean up the summary - remove excessive whitespace
                summary = re.sub(r'\n{3,}', '\n\n', summary)
                return summary
    
    # If no summary section found, try to extract introduction
    # Find the first major heading (## or #) and get content before it
    first_heading_match = re.search(r'^#+\s+', content, re.MULTILINE)
    if first_heading_match:
        intro_end = first_heading_match.start()
        intro = content[:intro_end].strip()
        if intro and len(intro) > 100:
            # Clean up the introduction
            intro = re.sub(r'\n{3,}', '\n\n', intro)
            # Limit to reasonable length (1000 chars)
            if len(intro) > 1000:
                intro = intro[:1000].rsplit(' ', 1)[0] + "..."
            return intro
    
    # Fallback: use first 800-1000 characters
    fallback = content[:1000].strip()
    if len(content) > 1000:
        # Try to end at a sentence boundary
        last_period = fallback.rfind('.')
        last_newline = fallback.rfind('\n')
        cutoff = max(last_period, last_newline)
        if cutoff > 500:  # Only use if we have substantial content
            fallback = fallback[:cutoff + 1]
        else:
            fallback = content[:800].rsplit(' ', 1)[0] + "..."
    
    return fallback


def create_settings_snapshot(request: ReportLensRequest) -> dict:
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


async def get_research_report(request: ReportLensRequest, user_id: str, api_key_id: str | None = None) -> dict:
    if user_id and api_key_id:
        await check_rate_limit(api_key_id, user_id)

    settings_snapshot = create_settings_snapshot(request)
    
    # Preprocess query: decompose if needed, enhance for synthesis
    try:
        llm = get_llm(settings_snapshot=settings_snapshot)
        preprocessed = preprocess_query_for_research(
            raw_query=request.query,
            llm=llm,
            mode="reportlens",
            max_sub_queries=5
        )
    except Exception as e:
        logger.warning(f"Failed to preprocess query (LLM error): {e}, using query as-is")
        # Fallback: use original query without decomposition
        preprocessed = {
            "search_queries": [request.query],
            "synthesis_prompt": enhance_reportlens_prompt(request.query),
            "original_query": request.query,
            "was_decomposed": False
        }
    
    quality = normalize_quality(getattr(request.settings, "quality", None))
    quality_preset = QUALITY_PRESETS[quality]

    # Use decomposed queries for search, enhanced prompt for synthesis
    result = generate_report(
        query=preprocessed["synthesis_prompt"],  # Use enhanced prompt for synthesis
        search_queries=preprocessed["search_queries"],  # Use decomposed queries for search
        search_tool=None,  # Let settings_snapshot determine the search tool
        max_results=quality_preset["max_results"],
        iterations=quality_preset["iterations"],
        searches_per_section=0,  # Match streaming endpoint
        is_research_subsection=quality_preset["is_research_subsection"],
        settings_snapshot=settings_snapshot,
    )
    serial = to_serializable(result)
    content = serial.get("content") or ""
    research_id = str(uuid.uuid4())
    report_format = normalize_report_format(
        getattr(request.settings, "report_format", "md")
    )
    provider = normalize_provider_name(
        os.getenv("TEKK_LLM_PROVIDER")
        or os.getenv("LDR_LLM_PROVIDER")
        or os.getenv("USE_MODEL")
        or "gemini"
    ).upper()
    model = provider_model(
        provider,
        os.getenv("TEKK_LLM_MODEL") or os.getenv("LDR_LLM_MODEL"),
    )
    try:
        total_tokens = max(1, round(len(content) / 4))
        input_tokens = max(1, round(total_tokens * 0.7))
        output_tokens = max(1, round(total_tokens * 0.3))
        # Ensure they sum to total_tokens
        if input_tokens + output_tokens != total_tokens:
            output_tokens = total_tokens - input_tokens
        if input_tokens + output_tokens != total_tokens:
            output_tokens = total_tokens - input_tokens
        credits_used = compute_credits_used(input_tokens, output_tokens, "TEKKSCOPE", "reportlens")
        download_info = await _create_report_download(
            content,
            request.query,
            user_id,
            report_format,
            research_id,
        )
        supabase.table("research_outputs").insert({
            "user_id": user_id,
            "research_id": research_id,
            "mode": "reportlens",
            "query": request.query,
            "summary": content[:500],
            "formatted_findings": content,
            "findings": None,
            "sources": None,
            "model": model,
            "provider": provider,
        }).execute()
        supabase.table("usage").insert({
            "user_id": user_id,
            "service_used": "reportlens",
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
        serial.update(download_info)
    except Exception as error:
        logger.warning("Report export failed for {}: {}", research_id, error)
        serial["export_error"] = str(error)
    return serial


async def stream_research_report(query: str, client_id: str, user_id: str, api_key_id: str | None = None, file_format: str = "pdf", is_research_subsection: bool = False) -> None:
    # Check rate limit and send error to client if exceeded
    if client_id and api_key_id:
        try:
            await check_rate_limit(api_key_id, user_id)
        except HTTPException as e:
            await manager.send_to_client(client_id, {"type": "error", "content": e.detail})
            await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
            return

    max_tokens = int(
        os.getenv("TEKK_LLM_MAX_TOKENS", os.getenv("LDR_LLM_MAX_TOKENS", "16000"))
    )
    provider = normalize_provider_name(
        os.getenv("TEKK_LLM_PROVIDER")
        or os.getenv("LDR_LLM_PROVIDER")
        or os.getenv("USE_MODEL")
        or "gemini"
    )
    model = provider_model(
        provider,
        os.getenv("TEKK_LLM_MODEL") or os.getenv("LDR_LLM_MODEL"),
    )
    overrides = provider_overrides_from_env(
        max_tokens=max_tokens,
        temperature=0.7,
        search_tool="searxng",
        search_instance_url=os.getenv(
            "TEKK_SEARXNG_URL", "https://search.tekkscope.com"
        ),
    )
    overrides["llm.model"] = model
    settings_snapshot = ldr_create_settings_snapshot(overrides=overrides)

    try:
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "start", "iterations": 0, "query": query}})
        
        # Preprocess query: decompose if needed, enhance for synthesis
        try:
            llm = get_llm(settings_snapshot=settings_snapshot)
            preprocessed = preprocess_query_for_research(
                raw_query=query,
                llm=llm,
                mode="reportlens",
                max_sub_queries=5
            )
        except Exception as e:
            logger.warning(f"Failed to preprocess query (LLM error): {e}, using query as-is")
            # Fallback: use original query without decomposition
            preprocessed = {
                "search_queries": [query],
                "synthesis_prompt": enhance_reportlens_prompt(query),
                "original_query": query,
                "was_decomposed": False
            }
        
        # Use first search query for preview (or original if not decomposed)
        preview_query = preprocessed["search_queries"][0] if preprocessed["search_queries"] else query
        urls_preview = await search_searxng(preview_query, 8)
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "urls_preview", "iterations": 0, "query": query, "urls": [u.get("url") for u in urls_preview[:8]]}})
        
        if preprocessed["was_decomposed"]:
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "query_decomposition", "message": f"Decomposed query into {len(preprocessed['search_queries'])} search queries", "iterations": 0}})
        
        loop = asyncio.get_running_loop()
        def on_progress(message: str, progress: int, metadata: dict):
            # Filter out LLM start/end messages - these are too technical for users
            phase = metadata.get("phase", "progress")
            
            # Skip LLM technical messages
            if phase in ["llm_start", "llm_end"] or message in ["LLM start", "LLM end"]:
                return
            
            # Skip empty or low-value messages
            if not phase and not message:
                return
            
            stage = phase
            if phase in {"analysis", "search_complete", "final_filtering", "filtering_complete"}:
                stage = "search"
            elif phase in {"synthesis", "finalizing", "generating_subsection"}:
                stage = "finalizing"
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
        # Quality tier presets
        quality = "deep" if is_research_subsection else "standard"
        quality_preset = QUALITY_PRESETS[quality]
        max_results = quality_preset["max_results"]
        iterations = quality_preset["iterations"]
        
        result = await asyncio.to_thread(
            generate_report,
            query=preprocessed["synthesis_prompt"],  # Use enhanced prompt for synthesis
            search_queries=preprocessed["search_queries"],  # Use decomposed queries for search
            search_tool=None,  # Let settings_snapshot determine the search tool
            max_results=max_results,
            iterations=iterations,
            searches_per_section=0,  # Always 0 (parallel mode would handle this differently)
            is_research_subsection=quality_preset["is_research_subsection"],
            settings_snapshot=settings_snapshot,
            progress_callback=on_progress,
        )
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "finalizing", "iterations": 1, "query": query}})
        serial = to_serializable(result)
        
        # Extract content and format
        content = serial.get("content") or ""
        content = format_research_output(content)
        serial["content"] = content
        
        # Extract and send executive summary first
        executive_summary = extract_executive_summary(content)
        if executive_summary:
            logger.info(f"Sending executive summary for client {client_id}")
            await manager.send_to_client(client_id, {
                "type": "executive_summary",
                "content": executive_summary
            })
        else:
            logger.warning(f"No executive summary extracted for client {client_id}")
        
        # Calculate credits
        total_tokens = max(1, round(len(content) / 4))
        input_tokens = max(1, round(total_tokens * 0.7))
        output_tokens = max(1, round(total_tokens * 0.3))
        # Ensure they sum to total_tokens
        if input_tokens + output_tokens != total_tokens:
            output_tokens = total_tokens - input_tokens
        if input_tokens + output_tokens != total_tokens:
            output_tokens = total_tokens - input_tokens
        credits_used = compute_credits_used(input_tokens, output_tokens, "TEKKSCOPE", "reportlens")
        provider = provider.upper()
        research_id = str(uuid.uuid4())
        
        # Generate file in requested format
        file_extension = normalize_report_format(file_format, default="pdf")
        
        # Generate file in requested format
        await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "generating_file", "message": f"Creating {file_extension.upper()} file..."}})
        
        try:
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "uploading", "message": "Uploading report..."}})
            download_info = await _create_report_download(
                content,
                query,
                client_id,
                file_extension,
                research_id,
            )
            
            # Store metadata in database
            supabase.table("research_outputs").insert({
                "user_id": user_id,
                "research_id": research_id,
                "mode": "reportlens",
                "query": query,
                "summary": content[:500],
                "formatted_findings": content,
                "findings": None,
                "sources": None,
                "model": model,
                "provider": provider,
            }).execute()
            
            # Track usage
            supabase.table("usage").insert({
                "user_id": user_id,
                "service_used": "reportlens",
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
            
            # Send download button as a separate distinct message.
            await manager.send_to_client(
                client_id,
                {"type": "response", "content": {"download": download_info}},
            )
            
            # Send citations if available
            try:
                citations = serial.get("sources")
                if citations:
                    await manager.send_to_client(client_id, {"type": "response", "content": {"citations": citations}})
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Error in reportlens file generation/upload: {str(e)}", exc_info=True)
            error_msg = f"Report generation failed: {str(e)}"
            if "upload" in str(e).lower() or "storage" in str(e).lower():
                error_msg = f"Failed to upload report to storage: {str(e)}"
            await manager.send_to_client(client_id, {"type": "error", "content": error_msg})
        
        await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
        await manager.send_to_client(client_id, "[END_OF_STREAM]")
    except Exception:
        await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
        await manager.send_to_client(client_id, "[END_OF_STREAM]")
        raise
