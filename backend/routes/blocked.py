"""Blocklist endpoints."""
from fastapi import APIRouter, HTTPException

from backend.schemas import BlockCompanyRequest, BlockedCompanyRead
from src.storage.lead_store import (
    block_company,
    unblock_company,
    get_blocked_companies,
)

router = APIRouter(tags=["blocked"])


@router.get("/blocked")
def list_blocked() -> list[BlockedCompanyRead]:
    return [BlockedCompanyRead(**bc) for bc in get_blocked_companies()]


@router.post("/blocked", status_code=201)
def add_blocked(body: BlockCompanyRequest):
    block_company(body.company_name, reason=body.reason)
    return {"ok": True}


@router.delete("/blocked/{company_name}")
def remove_blocked(company_name: str):
    unblock_company(company_name)
    return {"ok": True}
