from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import re

from src.models.lead import Lead, Sector, CompanyType
from src.storage.database import get_connection
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COMPANY_SUFFIXES = re.compile(
    r"\b(inc\.?|corp\.?|corporation|ltd\.?|llc|l\.l\.c\.?|limited|co\.?|"
    r"company|group|holdings|gmbh|ag|s\.?a\.?|s\.?r\.?l\.?|plc|pty\.?|"
    r"technologies|technology|tech|systems|solutions|robotics|ai)\s*$",
    re.IGNORECASE,
)


def _normalize_company_name(name: str) -> str:
    """Normalize a company name for dedup comparison.

    Strips suffixes like Inc, Corp, Ltd, LLC, etc. and lowercases.
    Falls back to the original name if stripping would produce empty string.
    """
    n = name.strip()
    if not n:
        return ""
    original_lower = n.lower()
    for _ in range(3):
        prev = n
        n = _COMPANY_SUFFIXES.sub("", n).strip().rstrip(",").strip()
        if n == prev:
            break
    result = n.lower()
    return result if result else original_lower


def _safe_enum(enum_cls, value, default):
    try:
        return enum_cls(value)
    except (ValueError, KeyError):
        return default


def _row_to_lead(row: dict) -> Lead:
    return Lead(
        id=row["id"],
        company_name=row["company_name"],
        sector=_safe_enum(Sector, row["sector"], Sector.OTHER),
        company_type=_safe_enum(CompanyType, row["company_type"], CompanyType.UNKNOWN),
        funding_stage=row.get("funding_stage"),
        product_name=row["product_name"],
        location=row.get("location"),
        website_url=row["website_url"],
        source_url=row["source_url"],
        source_type=row.get("source_type", "web_search"),
        tech_stack=json.loads(row["tech_stack"]) if row["tech_stack"] else [],
        jetson_usage=row.get("jetson_usage"),
        jetson_models=json.loads(row["jetson_models"]) if row["jetson_models"] else [],
        jetson_confirmed=bool(row["jetson_confirmed"]),
        user_rating=row.get("user_rating"),
        feedback=row.get("feedback"),
        campaign=row["campaign"],
        summary=row.get("summary") or "",
        discovered_at=datetime.fromisoformat(row["discovered_at"]),
    )


# ---------------------------------------------------------------------------
# Leads CRUD
# ---------------------------------------------------------------------------

def save_leads(leads: list[Lead], campaign: str) -> dict:
    saved = 0
    skipped = 0
    with get_connection() as conn:
        existing_rows = conn.execute(
            "SELECT company_name FROM leads WHERE campaign=?", (campaign,)
        ).fetchall()
        existing_normalized = {_normalize_company_name(r["company_name"]) for r in existing_rows}
        batch_normalized: set[str] = set()

        for lead in leads:
            lead.campaign = campaign
            norm = _normalize_company_name(lead.company_name)

            if norm in existing_normalized or norm in batch_normalized:
                skipped += 1
                logger.debug(f"Duplicate lead (normalized): {lead.company_name}")
                continue

            try:
                conn.execute(
                    """INSERT INTO leads
                    (company_name, sector, company_type, funding_stage, product_name,
                     location, website_url, source_url, source_type, tech_stack,
                     jetson_usage, jetson_models, jetson_confirmed,
                     campaign, summary, discovered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        lead.company_name,
                        lead.sector.value,
                        lead.company_type.value,
                        lead.funding_stage,
                        lead.product_name,
                        lead.location,
                        lead.website_url,
                        lead.source_url,
                        lead.source_type,
                        json.dumps(lead.tech_stack),
                        lead.jetson_usage,
                        json.dumps(lead.jetson_models),
                        int(lead.jetson_confirmed),
                        lead.campaign,
                        lead.summary,
                        lead.discovered_at.isoformat(),
                    ),
                )
                saved += 1
                batch_normalized.add(norm)
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    skipped += 1
                    logger.debug(f"Duplicate lead: {lead.company_name}")
                else:
                    raise
        conn.commit()
        logger.info(f"Saved {saved} leads, skipped {skipped} duplicates")
    return {"saved": saved, "skipped": skipped}


def get_feed(campaign: str = "", limit: int = 50, offset: int = 0) -> list[Lead]:
    with get_connection() as conn:
        if campaign:
            rows = conn.execute(
                """SELECT * FROM leads WHERE campaign=? AND user_rating IS NULL
                   AND company_name COLLATE NOCASE NOT IN (SELECT company_name COLLATE NOCASE FROM blocked_companies)
                   ORDER BY discovered_at DESC LIMIT ? OFFSET ?""",
                (campaign, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM leads WHERE user_rating IS NULL
                   AND company_name COLLATE NOCASE NOT IN (SELECT company_name COLLATE NOCASE FROM blocked_companies)
                   ORDER BY discovered_at DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [_row_to_lead(dict(r)) for r in rows]


def get_rated_leads(campaign: str = "", limit: int = 200) -> list[Lead]:
    with get_connection() as conn:
        if campaign:
            rows = conn.execute(
                "SELECT * FROM leads WHERE campaign=? AND user_rating IS NOT NULL ORDER BY user_rating DESC, discovered_at DESC LIMIT ?",
                (campaign, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM leads WHERE user_rating IS NOT NULL ORDER BY user_rating DESC, discovered_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_lead(dict(r)) for r in rows]


def get_lead(lead_id: int) -> Optional[Lead]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return _row_to_lead(dict(row)) if row else None


_ALLOWED_UPDATE_FIELDS = frozenset({
    "company_name", "sector", "company_type", "funding_stage", "product_name",
    "location", "website_url", "source_url", "source_type", "tech_stack",
    "jetson_usage", "jetson_models", "jetson_confirmed", "user_rating",
    "feedback", "summary",
})


def update_lead(lead_id: int, **kwargs) -> None:
    bad_keys = set(kwargs.keys()) - _ALLOWED_UPDATE_FIELDS
    if bad_keys:
        raise ValueError(f"Invalid field(s): {bad_keys}")

    with get_connection() as conn:
        json_fields = ("tech_stack", "jetson_models")
        for field in json_fields:
            if field in kwargs and not isinstance(kwargs[field], str):
                kwargs[field] = json.dumps(kwargs[field])
        if "jetson_confirmed" in kwargs and isinstance(kwargs["jetson_confirmed"], bool):
            kwargs["jetson_confirmed"] = int(kwargs["jetson_confirmed"])
        if "sector" in kwargs and isinstance(kwargs["sector"], Sector):
            kwargs["sector"] = kwargs["sector"].value
        if "company_type" in kwargs and isinstance(kwargs["company_type"], CompanyType):
            kwargs["company_type"] = kwargs["company_type"].value

        set_clause = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [lead_id]
        conn.execute(f"UPDATE leads SET {set_clause} WHERE id=?", values)
        conn.commit()


def set_rating(lead_id: int, rating: int) -> None:
    if not (1 <= rating <= 5):
        raise ValueError(f"Rating must be 1-5, got {rating}")
    update_lead(lead_id, user_rating=rating)


def set_feedback(lead_id: int, feedback: str) -> None:
    update_lead(lead_id, feedback=feedback)


def delete_lead(lead_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
        conn.commit()


def count_leads(campaign: str = "") -> int:
    with get_connection() as conn:
        if campaign:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM leads WHERE campaign=?", (campaign,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) as cnt FROM leads").fetchone()
        return row["cnt"]


def get_stats(campaign: str = "") -> dict:
    with get_connection() as conn:
        where = "WHERE campaign=?" if campaign else "WHERE 1=1"
        params = (campaign,) if campaign else ()
        row = conn.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN user_rating IS NOT NULL THEN 1 ELSE 0 END) as rated,
                SUM(CASE WHEN user_rating IS NULL AND company_name COLLATE NOCASE NOT IN
                    (SELECT company_name COLLATE NOCASE FROM blocked_companies) THEN 1 ELSE 0 END) as queue
            FROM leads {where}
        """, params).fetchone()
        return {"total": row["total"], "rated": row["rated"], "queue": row["queue"]}


def get_existing_company_names(campaign: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT company_name FROM leads WHERE campaign=?", (campaign,)
        ).fetchall()
        return [r["company_name"] for r in rows]


# ---------------------------------------------------------------------------
# Blocked Companies
# ---------------------------------------------------------------------------

def block_company(company_name: str, reason: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO blocked_companies (company_name, blocked_at, reason) VALUES (?, ?, ?)",
            (company_name.strip(), datetime.now(timezone.utc).isoformat(), reason),
        )
        conn.commit()


def unblock_company(company_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM blocked_companies WHERE company_name=? COLLATE NOCASE",
            (company_name.strip(),),
        )
        conn.commit()


def get_blocked_company_names() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT company_name FROM blocked_companies ORDER BY blocked_at DESC").fetchall()
        return [r["company_name"] for r in rows]


def get_blocked_companies() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT company_name, blocked_at, reason FROM blocked_companies ORDER BY blocked_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
