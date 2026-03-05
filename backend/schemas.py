"""Pydantic schemas for API request/response models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LeadRead(BaseModel):
    id: int
    company_name: str
    sector: str
    company_type: str
    funding_stage: Optional[str] = None
    product_name: str
    location: Optional[str] = None
    website_url: str
    source_url: str
    source_type: str
    tech_stack: list[str]
    jetson_usage: Optional[str] = None
    jetson_models: list[str]
    jetson_confirmed: bool
    user_rating: Optional[int] = None
    feedback: Optional[str] = None
    campaign: str
    summary: str
    discovered_at: str


class LeadUpdate(BaseModel):
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    website_url: Optional[str] = None
    feedback: Optional[str] = None


class StatsRead(BaseModel):
    total: int
    rated: int
    queue: int


class CampaignRead(BaseModel):
    name: str
    filename: str
    description: str


class CampaignCreate(BaseModel):
    name: str
    description: str


class BlockCompanyRequest(BaseModel):
    company_name: str
    reason: str = ""


class BlockedCompanyRead(BaseModel):
    company_name: str
    blocked_at: str
    reason: str


class ResearchRequest(BaseModel):
    campaign: Optional[str] = None
    prompt: Optional[str] = None
    provider: str = "gemini"


class ResearchJobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float = 0.0
    phase: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None


class ProviderInfo(BaseModel):
    name: str
    has_key: bool
