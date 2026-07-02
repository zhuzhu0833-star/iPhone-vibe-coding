"""Data models for the daily digest pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawArticle:
    title: str
    link: str
    summary: str
    published: datetime | None
    source_name: str
    source_type: str
    country_id: str
    country_name: str
    country_flag: str


@dataclass
class DigestItem:
    title_en: str
    summary_en: str
    summary_zh: str
    link: str
    source_name: str
    source_type: str
    country_id: str
    country_name: str
    country_flag: str
    category: str
    score: float = 0.0
    action_advice: str = ""


@dataclass
class Digest:
    date_label: str
    items: list[DigestItem] = field(default_factory=list)
    slot: str = "morning"
    disclaimer: str = (
        "This digest is for informational purposes only and does not constitute "
        "legal or immigration advice. Please refer to official sources."
    )

    @property
    def disclaimer_zh(self) -> str:
        return "本简报仅供参考，不构成法律或移民建议，请以官方信息为准。"

    @property
    def slot_label_zh(self) -> str:
        return "早报" if self.slot == "morning" else "晚报"

    @property
    def slot_focus_zh(self) -> str:
        if self.slot == "morning":
            return "招生数据 · 政策动向"
        return "申请截止 · 签证工签"
