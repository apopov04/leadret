from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Campaign(BaseModel):
    name: str
    description: str = ""
    blocklist: list[str] = Field(default_factory=list)
    exclude_domains: list[str] = Field(default_factory=list)

    @classmethod
    def from_adhoc(cls, prompt: str) -> Campaign:
        """Create a campaign from a free-text prompt."""
        return cls(name="adhoc", description=prompt)


def load_campaign(campaign_name: str) -> Campaign:
    """Load a campaign from a YAML file in the campaigns/ directory."""
    base = Path(__file__).resolve().parent.parent.parent / "campaigns"
    path = base / f"{campaign_name}.yaml"
    if not path.exists():
        path = base / f"{campaign_name}.yml"
    if not path.exists():
        raise FileNotFoundError(f"Campaign file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Campaign(**data)


def list_campaigns() -> list[str]:
    """List available campaign names."""
    base = Path(__file__).resolve().parent.parent.parent / "campaigns"
    if not base.exists():
        return []
    names = []
    for p in sorted(base.iterdir()):
        if p.suffix in (".yaml", ".yml"):
            names.append(p.stem)
    return names
