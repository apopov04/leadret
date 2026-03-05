"""Lead CRUD endpoints."""
from fastapi import APIRouter, HTTPException, Query

from backend.schemas import LeadRead, LeadUpdate
from src.storage.lead_store import (
    get_feed,
    get_rated_leads,
    get_lead,
    set_rating,
    update_lead,
    delete_lead,
)

router = APIRouter(tags=["leads"])


def _lead_to_response(lead) -> dict:
    return LeadRead(
        id=lead.id,
        company_name=lead.company_name,
        sector=lead.sector.value,
        company_type=lead.company_type.value,
        funding_stage=lead.funding_stage,
        product_name=lead.product_name,
        location=lead.location,
        website_url=lead.website_url,
        source_url=lead.source_url,
        source_type=lead.source_type,
        tech_stack=lead.tech_stack,
        jetson_usage=lead.jetson_usage,
        jetson_models=lead.jetson_models,
        jetson_confirmed=lead.jetson_confirmed,
        user_rating=lead.user_rating,
        feedback=lead.feedback,
        campaign=lead.campaign,
        summary=lead.summary,
        discovered_at=lead.discovered_at.isoformat(),
    ).model_dump()


@router.get("/leads/queue")
def list_queue(
    campaign: str = Query(""),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    leads = get_feed(campaign, limit=limit, offset=offset)
    return [_lead_to_response(l) for l in leads]


@router.get("/leads/rated")
def list_rated(
    campaign: str = Query(""),
    limit: int = Query(200, ge=1, le=500),
):
    leads = get_rated_leads(campaign, limit=limit)
    return [_lead_to_response(l) for l in leads]


@router.get("/leads/{lead_id}")
def read_lead(lead_id: int):
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _lead_to_response(lead)


@router.patch("/leads/{lead_id}")
def patch_lead(lead_id: int, body: LeadUpdate):
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "user_rating" in updates and updates["user_rating"] is not None:
        set_rating(lead_id, updates.pop("user_rating"))

    if updates:
        update_lead(lead_id, **updates)

    return _lead_to_response(get_lead(lead_id))


@router.delete("/leads/{lead_id}")
def remove_lead(lead_id: int):
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    delete_lead(lead_id)
    return {"ok": True}
