"""Persist digest between workflow steps (generate → deploy → notify)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.models import Digest, DigestItem

DIGEST_JSON = Path("digests/digest.json")


def save_digest_json(digest: Digest) -> Path:
    DIGEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date_label": digest.date_label,
        "slot": digest.slot,
        "items": [asdict(item) for item in digest.items],
    }
    DIGEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return DIGEST_JSON


def load_digest_json() -> Digest:
    data = json.loads(DIGEST_JSON.read_text(encoding="utf-8"))
    items = [DigestItem(**item) for item in data.get("items", [])]
    return Digest(
        date_label=data["date_label"],
        items=items,
        slot=data.get("slot", "morning"),
    )
