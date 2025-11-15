import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.clients.nlts_client import process_nlts_request

router = APIRouter()
logger = logging.getLogger(__name__)

class NLTSRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2_000)
    schema: Optional[Dict[str, Any]] = None

class NLTSResponse(BaseModel):
    structured_output: Any  # Can be Dict or List
    schema_used: Dict[str, Any]
    research_summary: Optional[str] = None

@router.post("/", response_model=NLTSResponse)
async def nlts_endpoint(request: NLTSRequest):
    """
    Natural Language to Structured JSON endpoint.
    
    Accepts a natural language query and an optional JSON schema.
    Performs research and returns structured data matching the schema.
    If no schema is provided, one is inferred from the query.
    """
    try:
        result = await process_nlts_request(request.query, request.schema)
        return result
    except Exception:
        logger.exception("NLTS request failed")
        raise HTTPException(status_code=500, detail="Structured research failed") from None
