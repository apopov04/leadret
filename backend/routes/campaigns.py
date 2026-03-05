"""Campaign CRUD endpoints."""
import re
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from backend.schemas import CampaignCreate, CampaignRead
from src.models.campaign import list_campaigns, load_campaign

router = APIRouter(tags=["campaigns"])

CAMPAIGNS_DIR = Path(__file__).resolve().parent.parent.parent / "campaigns"


def _slugify(name: str) -> str:
    """Turn a campaign name into a safe filename slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "campaign"


@router.get("/campaigns")
def get_campaigns() -> list[CampaignRead]:
    result = []
    for fname in list_campaigns():
        try:
            c = load_campaign(fname)
            result.append(CampaignRead(
                name=c.name,
                filename=fname,
                description=c.description,
            ))
        except Exception:
            continue
    return result


@router.post("/campaigns", status_code=201)
def create_campaign(body: CampaignCreate) -> CampaignRead:
    if not body.name.strip():
        raise HTTPException(400, "Campaign name is required")
    if not body.description.strip():
        raise HTTPException(400, "Campaign description is required")

    slug = _slugify(body.name)
    path = CAMPAIGNS_DIR / f"{slug}.yaml"

    if path.exists():
        raise HTTPException(409, f"Campaign '{slug}' already exists")

    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "name": body.name.strip(),
        "description": body.description.strip(),
        "exclude_domains": [],
        "blocklist": [],
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return CampaignRead(name=data["name"], filename=slug, description=data["description"])


@router.patch("/campaigns/{filename}")
def update_campaign(filename: str, body: CampaignCreate) -> CampaignRead:
    if not re.match(r"^[a-z0-9-]+$", filename):
        raise HTTPException(400, "Invalid campaign filename")

    path = CAMPAIGNS_DIR / f"{filename}.yaml"
    if not path.exists():
        path = CAMPAIGNS_DIR / f"{filename}.yml"
    if not path.exists():
        raise HTTPException(404, "Campaign not found")

    # Load existing to preserve blocklist/exclude_domains
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    data["name"] = body.name.strip()
    data["description"] = body.description.strip()

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return CampaignRead(name=data["name"], filename=filename, description=data["description"])


@router.delete("/campaigns/{filename}", status_code=204)
def delete_campaign(filename: str):
    # Sanitize: only allow simple slugs
    if not re.match(r"^[a-z0-9-]+$", filename):
        raise HTTPException(400, "Invalid campaign filename")

    path = CAMPAIGNS_DIR / f"{filename}.yaml"
    if not path.exists():
        path = CAMPAIGNS_DIR / f"{filename}.yml"
    if not path.exists():
        raise HTTPException(404, "Campaign not found")

    path.unlink()
    return None
