"""Dependency-free Model Context Protocol server for Tekkscope.

The server uses the MCP stdio transport: one JSON-RPC message per line on
stdin and one response per line on stdout. It keeps Tekkscope imports lazy so
tool discovery does not initialize the crawler, LLM, database, or report
stacks.

Run from the ``backend`` directory with ``python -m app.mcp_server``.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import socket
import sys
from ipaddress import ip_address
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import urlparse


LOGGER = logging.getLogger(__name__)
MCP_PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26"}
SERVER_NAME = "tekkscope"
SERVER_VERSION = "0.1.0"

REPORT_MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}


TOOL_DEFINITIONS = [
    {
        "name": "tekkscope_search",
        "description": (
            "Search the configured SearXNG instance for web results. "
            "Results are deduplicated and capped by Tekkscope's existing limits."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The web search query."},
                "num_results": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of results to return.",
                    "default": 10,
                },
                "n_queries": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of generated queries when enhanced_search is enabled.",
                    "default": 3,
                },
                "enhanced_search": {
                    "type": "boolean",
                    "description": "Use the configured LLM to generate diverse search queries.",
                    "default": False,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tekkscope_browse_url",
        "description": (
            "Open a web page with Tekkscope's Playwright/Crawlee browser and "
            "return cleaned text, metadata, and internal/external links."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "HTTP or HTTPS URL to browse."},
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tekkscope_extract_urls",
        "description": (
            "Extract structured content from multiple HTTP or HTTPS URLs "
            "using the existing concurrent Playwright/Crawlee pipeline."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "URLs to browse and enrich with extracted content.",
                },
            },
            "required": ["urls"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tekkscope_search_and_extract",
        "description": (
            "Search SearXNG and extract page text from the returned sources "
            "within Tekkscope's existing scrape deadline."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "num_results": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of sources to process.",
                    "default": 10,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tekkscope_get_research_sources",
        "description": (
            "Retrieve the saved source records associated with a Tekkscope "
            "research ID from the existing research-source service."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "research_id": {
                    "type": "string",
                    "description": "Research UUID or identifier.",
                },
                "username": {
                    "type": "string",
                    "description": "Optional database username; defaults to TEKK_MCP_USERNAME.",
                },
            },
            "required": ["research_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tekkscope_generate_report",
        "description": (
            "Generate a research report using the existing ReportLens pipeline. "
            "Without user_id this is stateless; with user_id it uses the existing "
            "persisted ReportLens path and may return a download URL."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Research topic or question."},
                "file_format": {
                    "type": "string",
                    "enum": ["pdf", "docx", "md"],
                    "description": "Requested report format.",
                    "default": "md",
                },
                "quality": {
                    "type": "string",
                    "enum": ["standard", "deep"],
                    "description": "Report research depth.",
                    "default": "standard",
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional user ID; defaults to TEKK_MCP_USER_ID for persisted reports.",
                },
                "api_key_id": {
                    "type": "string",
                    "description": "Optional API key ID used by the existing rate limiter.",
                },
                "include_file": {
                    "type": "boolean",
                    "description": "Include the generated file as base64; stateless PDF/DOCX requests include it automatically.",
                    "default": False,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tekkscope_export_report",
        "description": (
            "Convert Markdown report content to PDF, DOCX, or Markdown using "
            "Tekkscope's existing report export pipeline."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "markdown": {"type": "string", "description": "Markdown report content."},
                "file_format": {
                    "type": "string",
                    "enum": ["pdf", "docx", "md"],
                    "description": "Output format.",
                    "default": "md",
                },
                "title": {
                    "type": "string",
                    "description": "Document title.",
                    "default": "Research Report",
                },
            },
            "required": ["markdown"],
            "additionalProperties": False,
        },
    },
]


class ToolInputError(ValueError):
    """Raised when an MCP tool receives invalid arguments."""


def _require_string(arguments: Dict[str, Any], key: str, max_length: int = 8_000) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolInputError(f"'{key}' must be a non-empty string")
    value = value.strip()
    if len(value) > max_length:
        raise ToolInputError(f"'{key}' cannot exceed {max_length} characters")
    return value


def _optional_string(arguments: Dict[str, Any], key: str) -> Optional[str]:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolInputError(f"'{key}' must be a string when provided")
    value = value.strip()
    return value or None


def _optional_int(
    arguments: Dict[str, Any], key: str, default: int, maximum: int | None = None
) -> int:
    value = arguments.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ToolInputError(f"'{key}' must be an integer")
    if value < 1:
        raise ToolInputError(f"'{key}' must be at least 1")
    if maximum is not None and value > maximum:
        raise ToolInputError(f"'{key}' cannot exceed {maximum}")
    return value


def _optional_bool(arguments: Dict[str, Any], key: str, default: bool) -> bool:
    value = arguments.get(key, default)
    if not isinstance(value, bool):
        raise ToolInputError(f"'{key}' must be a boolean")
    return value


def _validate_http_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ToolInputError("'url' must be an absolute HTTP or HTTPS URL")

    hostname = parsed.hostname
    if not hostname:
        raise ToolInputError("'url' must contain a hostname")
    normalized_host = hostname.rstrip(".").lower()
    blocked_names = {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata.google.com",
    }
    if normalized_host in blocked_names or normalized_host.endswith((".local", ".internal")):
        raise ToolInputError("'url' must target a public host")

    try:
        resolved_addresses = {
            ip_address(info[4][0])
            for info in socket.getaddrinfo(normalized_host, parsed.port, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError):
        raise ToolInputError("'url' hostname could not be resolved") from None
    if not resolved_addresses or any(not address.is_global for address in resolved_addresses):
        raise ToolInputError("'url' must target a public host")
    return value


def _validate_url_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ToolInputError("'urls' must be a non-empty array")
    if len(value) > 50:
        raise ToolInputError("'urls' cannot contain more than 50 URLs")
    urls = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ToolInputError("Each value in 'urls' must be a non-empty string")
        item = item.strip()
        if len(item) > 4_000:
            raise ToolInputError("Each URL cannot exceed 4000 characters")
        urls.append(_validate_http_url(item))
    return urls


def _normalize_report_format(value: Optional[str]) -> str:
    normalized = (value or "md").strip().lower()
    if normalized == "markdown":
        normalized = "md"
    if normalized not in REPORT_MIME_TYPES:
        raise ToolInputError("'file_format' must be one of: pdf, docx, md")
    return normalized


def _normalize_quality(value: Optional[str]) -> str:
    normalized = (value or "standard").strip().lower()
    if normalized not in {"standard", "deep"}:
        raise ToolInputError("'quality' must be one of: standard, deep")
    return normalized


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _safe_filename(title: str, extension: str) -> str:
    safe = "".join(
        char if char.isalnum() or char in {"-", "_"} else "-" for char in title
    )
    safe = "-".join(part for part in safe.split("-") if part)[:80]
    return f"{safe or 'research-report'}.{extension}"


async def _search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.clients.search import search_links

    query = _require_string(arguments, "query", max_length=2_000)
    num_results = _optional_int(arguments, "num_results", 10, maximum=100)
    n_queries = _optional_int(arguments, "n_queries", 3, maximum=10)
    enhanced_search = _optional_bool(arguments, "enhanced_search", False)
    results = await search_links(query, n_queries, num_results, enhanced_search)
    return {"query": query, "results": results}


async def _browse_url(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.clients.scraper import extract_content_from_url

    url = _validate_http_url(_require_string(arguments, "url", max_length=4_000))
    result = await extract_content_from_url(url)
    if isinstance(result, dict):
        result.setdefault("url", url)
    return result


async def _extract_urls(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.clients.scraper import extract_content_from_links

    urls = _validate_url_list(arguments.get("urls"))
    results = await extract_content_from_links([{"url": url} for url in urls])
    return {"results": results}


async def _search_and_extract(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.clients.scraper import search_and_extract

    query = _require_string(arguments, "query", max_length=2_000)
    num_results = _optional_int(arguments, "num_results", 10, maximum=100)
    content = await search_and_extract(query, num_results)
    return {
        "query": query,
        "results": [
            {"url": url, "content": page_content}
            for url, page_content in content.items()
        ],
    }


async def _get_research_sources(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.research_lib.web.services.research_sources_service import (
        ResearchSourcesService,
    )

    research_id = _require_string(arguments, "research_id")
    username = _optional_string(arguments, "username") or os.getenv("TEKK_MCP_USERNAME")
    sources = await asyncio.to_thread(
        ResearchSourcesService.get_research_sources,
        research_id,
        username,
    )
    return {"research_id": research_id, "sources": sources}


async def _generate_report(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.clients.reportlens_client import (
        QUALITY_PRESETS,
        create_settings_snapshot,
        get_research_report,
    )
    from app.models.api_models import ReportLensRequest, ResearchSettings

    query = _require_string(arguments, "query", max_length=2_000)
    file_format = _normalize_report_format(_optional_string(arguments, "file_format"))
    quality = _normalize_quality(_optional_string(arguments, "quality"))
    user_id = _optional_string(arguments, "user_id") or os.getenv("TEKK_MCP_USER_ID")
    api_key_id = _optional_string(arguments, "api_key_id") or os.getenv("TEKK_MCP_API_KEY_ID")
    include_file = _optional_bool(arguments, "include_file", False)
    include_file = include_file or (not user_id and file_format != "md")

    request = ReportLensRequest(
        query=query,
        settings=ResearchSettings(
            search_tool="searxng",
            report_format=file_format,
            quality=quality,
        ),
    )

    if user_id:
        # Reuse the complete ReportLens path, including persistence and storage.
        report = await get_research_report(request, user_id=user_id, api_key_id=api_key_id)
    else:
        # Keep the MCP server useful for local/stateless agents without inventing
        # a database user. The core report generator remains the source of truth.
        from app.research_lib.api.research_functions import generate_report
        from app.utils.response_utils import to_serializable

        preset = QUALITY_PRESETS[quality]
        settings_snapshot = create_settings_snapshot(request)
        report = await asyncio.to_thread(
            generate_report,
            query=query,
            search_tool=None,
            max_results=preset["max_results"],
            iterations=preset["iterations"],
            searches_per_section=0,
            is_research_subsection=preset["is_research_subsection"],
            settings_snapshot=settings_snapshot,
        )
        report = to_serializable(report)

    if not isinstance(report, dict):
        report = {"content": str(report)}

    result: Dict[str, Any] = {
        "query": query,
        "quality": quality,
        "file_format": file_format,
        "persisted": bool(user_id),
        "report": report,
    }

    if include_file:
        content = report.get("content") or ""
        if not isinstance(content, str):
            content = str(content)
        from app.utils.report_generator import generate_report_file

        file_bytes = await asyncio.to_thread(
            generate_report_file,
            content,
            file_format=file_format,
            title=query[:100],
        )
        result["file"] = {
            "filename": _safe_filename(query, file_format),
            "mime_type": REPORT_MIME_TYPES[file_format],
            "data_base64": base64.b64encode(file_bytes).decode("ascii"),
        }

    return result


async def _export_report(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from app.utils.report_generator import generate_report_file

    markdown = _require_string(arguments, "markdown")
    file_format = _normalize_report_format(_optional_string(arguments, "file_format"))
    title = _optional_string(arguments, "title") or "Research Report"
    file_bytes = await asyncio.to_thread(
        generate_report_file,
        markdown,
        file_format=file_format,
        title=title,
    )
    return {
        "filename": _safe_filename(title, file_format),
        "mime_type": REPORT_MIME_TYPES[file_format],
        "data_base64": base64.b64encode(file_bytes).decode("ascii"),
    }


TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
    "tekkscope_search": _search,
    "tekkscope_browse_url": _browse_url,
    "tekkscope_extract_urls": _extract_urls,
    "tekkscope_search_and_extract": _search_and_extract,
    "tekkscope_get_research_sources": _get_research_sources,
    "tekkscope_generate_report": _generate_report,
    "tekkscope_export_report": _export_report,
}


def _json_rpc_result(request_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _json_rpc_error(
    request_id: Any, code: int, message: str, data: Any = None
) -> Dict[str, Any]:
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


class TekkscopeMCPServer:
    """Small MCP JSON-RPC server backed by Tekkscope's existing services."""

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method")
        request_id = message.get("id")
        raw_params = message.get("params")
        params = {} if raw_params is None else raw_params

        if method == "initialize":
            requested_version = params.get("protocolVersion") if isinstance(params, dict) else None
            protocol_version = (
                requested_version
                if requested_version in SUPPORTED_PROTOCOL_VERSIONS
                else MCP_PROTOCOL_VERSION
            )
            return _json_rpc_result(
                request_id,
                {
                    "protocolVersion": protocol_version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    "instructions": (
                        "Use Tekkscope search and browsing tools for source-backed research; "
                        "use report tools for Markdown, PDF, or DOCX outputs."
                    ),
                },
            )

        # MCP notifications do not receive responses.
        if method in {
            "notifications/initialized",
            "notifications/cancelled",
            "notifications/progress",
        }:
            return None

        if method == "ping":
            return _json_rpc_result(request_id, {})

        if method == "tools/list":
            return _json_rpc_result(request_id, {"tools": TOOL_DEFINITIONS})

        if method == "tools/call":
            if not isinstance(params, dict):
                return _json_rpc_error(request_id, -32602, "tools/call params must be an object")
            name = params.get("name")
            raw_arguments = params.get("arguments")
            arguments = {} if raw_arguments is None else raw_arguments
            if not isinstance(name, str) or not name:
                return _json_rpc_error(request_id, -32602, "tools/call requires a tool name")
            if not isinstance(arguments, dict):
                return _json_rpc_error(request_id, -32602, "tool arguments must be an object")

            handler = TOOL_HANDLERS.get(name)
            if handler is None:
                return _json_rpc_error(request_id, -32602, f"Unknown tool: {name}")

            try:
                result = await handler(arguments)
                return _json_rpc_result(
                    request_id,
                    {"content": [{"type": "text", "text": _json_text(result)}]},
                )
            except ToolInputError as error:
                return _json_rpc_result(
                    request_id,
                    {
                        "isError": True,
                        "content": [{"type": "text", "text": str(error)}],
                    },
                )
            except Exception as error:  # noqa: BLE001 - MCP must return tool failures
                LOGGER.exception("MCP tool failed: %s", name)
                return _json_rpc_result(
                    request_id,
                    {
                        "isError": True,
                        "content": [
                            {"type": "text", "text": f"Tekkscope tool failed: {error}"}
                        ],
                    },
                )

        if request_id is None:
            return None
        return _json_rpc_error(request_id, -32601, f"Method not found: {method}")


async def serve_stdio() -> None:
    """Read newline-delimited JSON-RPC messages and write MCP responses."""

    server = TekkscopeMCPServer()
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            return
        if not line.strip():
            continue

        response: dict[str, Any] | None
        try:
            message = json.loads(line)
        except json.JSONDecodeError as error:
            response = _json_rpc_error(None, -32700, f"Invalid JSON: {error.msg}")
        else:
            if not isinstance(message, dict):
                response = _json_rpc_error(None, -32600, "JSON-RPC message must be an object")
            else:
                response = await server.handle_message(message)

        if response is not None:
            sys.stdout.write(_json_text(response) + "\n")
            sys.stdout.flush()


def main() -> None:
    """Run the Tekkscope MCP stdio server."""

    asyncio.run(serve_stdio())


if __name__ == "__main__":
    main()
