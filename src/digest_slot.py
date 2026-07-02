"""Resolve morning/evening digest slot (Beijing time)."""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")


def resolve_digest_slot() -> str:
    slot = os.environ.get("DIGEST_SLOT", "").strip().lower()
    if slot in ("morning", "evening"):
        return slot
    hour = datetime.now(BEIJING).hour
    return "morning" if hour < 18 else "evening"
