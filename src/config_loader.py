"""Load YAML configuration files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_sources() -> dict:
    with open(CONFIG_DIR / "sources.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    catalog = _load_json(DATA_DIR / "catalog.json")
    selections = _load_json(DATA_DIR / "selections.json")

    enabled_ids = set(selections.get("enabled_source_ids", []))
    custom_sources = selections.get("custom_sources", [])

    countries = []
    for country in catalog.get("countries", []):
        country_id = country["id"]
        sources = [
            {
                "name": source["name"],
                "type": source["type"],
                "url": source["url"],
            }
            for source in country.get("sources", [])
            if source["id"] in enabled_ids
        ]

        for custom in custom_sources:
            if custom.get("country_id") != country_id:
                continue
            sources.append(
                {
                    "name": custom["name"],
                    "type": custom.get("type", "university"),
                    "url": custom["url"],
                }
            )

        if sources:
            countries.append(
                {
                    "id": country_id,
                    "name": country["name"],
                    "flag": country.get("flag", ""),
                    "sources": sources,
                }
            )

    settings = config.get("settings", {})
    return {"settings": settings, "countries": countries}


def load_keywords() -> dict:
    with open(CONFIG_DIR / "keywords.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
