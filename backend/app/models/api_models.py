from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Reject unexpected request fields so clients catch integration mistakes early."""

    model_config = ConfigDict(extra="forbid")


class SearchRequest(StrictModel):
    query: str = Field(min_length=1, max_length=2_000)
    num_results: int = Field(default=10, ge=1, le=100)
    mode: str = Field(default="links", max_length=40)
    n_queries: int = Field(default=3, ge=1, le=10)
    enhanced_search: bool = False


class Metadata(StrictModel):
    font: Optional[str] = None
    colors: Optional[List[str]] = None


class InternalLink(StrictModel):
    text: str
    url: str


class ExternalLink(StrictModel):
    text: str
    url: str


class SearchResult(StrictModel):
    title: str
    url: str
    content: Optional[str] = None
    method: Optional[str] = None
    metadata: Optional[Metadata] = None
    internal_links: Optional[List[InternalLink]] = None
    external_links: Optional[List[ExternalLink]] = None


class SearchResponse(StrictModel):
    results: List[SearchResult]


class ResearchSettings(StrictModel):
    search_tool: str = Field(default="wikipedia", max_length=60)
    max_results: int = Field(default=5, ge=1, le=100)
    iteration_depth: int = Field(default=2, ge=1, le=10)
    report_format: str = Field(default="markdown", max_length=20)
    quality: str = Field(default="standard", max_length=20)


class LensRequest(StrictModel):
    query: str = Field(min_length=1, max_length=2_000)
    settings: ResearchSettings = Field(default_factory=ResearchSettings)


class DeepLensRequest(StrictModel):
    query: str = Field(min_length=1, max_length=2_000)
    settings: ResearchSettings = Field(default_factory=ResearchSettings)


class ReportLensRequest(StrictModel):
    query: str = Field(min_length=1, max_length=2_000)
    settings: ResearchSettings = Field(default_factory=ResearchSettings)


class ChatRequest(StrictModel):
    query: str = Field(min_length=1, max_length=8_000)
    mode: Optional[str] = Field(default="chat", max_length=40)


class ChatResponse(StrictModel):
    response: str


class ResearchResponse(StrictModel):
    result: dict
