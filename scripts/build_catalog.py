#!/usr/bin/env python3
"""Build data/catalog.json and default data/selections.json from sources catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "catalog.json"
SELECTIONS_PATH = ROOT / "data" / "selections.json"
LEGACY_SOURCES = ROOT / "config" / "sources.full.yaml"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:48] or "source"


def load_legacy_countries() -> list[dict]:
    if LEGACY_SOURCES.exists():
        path = LEGACY_SOURCES
    else:
        path = ROOT / "config" / "sources.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("countries", [])


def build_catalog() -> dict:
    catalog_countries = []
    for country in load_legacy_countries():
        country_id = country["id"]
        sources = []
        for src in country.get("sources", []):
            sources.append(
                {
                    "id": f"{country_id}-{slugify(src['name'])}",
                    "name": src["name"],
                    "type": src["type"],
                    "url": src["url"],
                }
            )
        catalog_countries.append(
            {
                "id": country_id,
                "name": country["name"],
                "flag": country.get("flag", ""),
                "sources": sources,
            }
        )
    return {"countries": catalog_countries}


def main() -> None:
    catalog = build_catalog()
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if SELECTIONS_PATH.exists():
        with open(SELECTIONS_PATH, encoding="utf-8") as f:
            selections = json.load(f)
    else:
        enabled_ids = [
            source["id"]
            for country in catalog["countries"]
            for source in country["sources"]
        ]
        selections = {"enabled_source_ids": enabled_ids, "custom_sources": []}

    with open(SELECTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(selections, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = sum(len(c["sources"]) for c in catalog["countries"])
    print(f"Wrote {CATALOG_PATH} ({total} sources)")
    print(f"Wrote {SELECTIONS_PATH}")


if __name__ == "__main__":
    main()
