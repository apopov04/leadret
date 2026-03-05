"""Stats endpoint."""
from fastapi import APIRouter, Query

from backend.schemas import StatsRead
from src.storage.lead_store import get_stats

router = APIRouter(tags=["stats"])


@router.get("/stats")
def read_stats(campaign: str = Query("")) -> StatsRead:
    return StatsRead(**get_stats(campaign))
