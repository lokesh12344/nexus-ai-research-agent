from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ResearchStep(BaseModel):
    step_number: int
    description: str
    search_query: Optional[str] = Field(default=None, description="Concise web search query (3-6 keywords) for search tool")
    tool: str = Field(description="Tool to use for this step, e.g., 'search', 'scrape'")

class ResearchPlan(BaseModel):
    query: str
    steps: List[ResearchStep]
    estimated_effort: str

class SourceQuality(Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_4 = "tier_4"

class Source(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    content_snippet: str
    relevance_score: float = Field(ge=0, le=1)
    quality: SourceQuality = Field(default=SourceQuality.TIER_4)
    published_date: Optional[str] = None

class Finding(BaseModel):
    claim: str
    supporting_urls: List[HttpUrl]
    evidence_passages: List[str]
    is_interpreted: bool

class ConfidenceBreakdown(BaseModel):
    source_relevance: float = Field(ge=0, le=1)
    source_authority: float = Field(ge=0, le=1)
    source_diversity: float = Field(ge=0, le=1)
    evidence_coverage: float = Field(ge=0, le=1)
    corroboration: float = Field(ge=0, le=1)

class FinalAnswer(BaseModel):
    question: str
    short_answer: str
    findings: List[Finding]
    source_urls: List[HttpUrl]
    confidence_level: ConfidenceLevel
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    calibration_status: str = Field("heuristic")
    assumptions: List[str]
    limitations: List[str]
    unanswered_questions: List[str]
