from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class CompanyType(str, enum.Enum):
    END_USER = "end_user"
    RESELLER = "reseller"
    MANUFACTURER = "manufacturer"
    SERVICE_PROVIDER = "service_provider"
    DISTRIBUTOR = "distributor"
    UNKNOWN = "unknown"


class Sector(str, enum.Enum):
    ROBOTICS = "robotics"
    AUTONOMOUS_VEHICLES = "autonomous_vehicles"
    INDUSTRIAL_AUTOMATION = "industrial_automation"
    SMART_CITIES = "smart_cities"
    HEALTHCARE = "healthcare"
    AGRICULTURE = "agriculture"
    RETAIL = "retail"
    DEFENSE = "defense"
    DRONES = "drones"
    EDGE_AI = "edge_ai"
    COMPUTER_VISION = "computer_vision"
    OTHER = "other"


class Lead(BaseModel):
    id: Optional[int] = None
    company_name: str
    sector: Sector = Sector.OTHER
    company_type: CompanyType = CompanyType.UNKNOWN
    funding_stage: Optional[str] = None
    product_name: str = ""
    location: Optional[str] = None
    website_url: str = ""
    source_url: str
    source_type: str = "web_search"
    tech_stack: list[str] = Field(default_factory=list)
    jetson_usage: Optional[str] = None
    jetson_models: list[str] = Field(default_factory=list)
    jetson_confirmed: bool = False
    user_rating: Optional[int] = None
    feedback: Optional[str] = None
    campaign: str = ""
    summary: str = ""
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
