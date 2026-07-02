"""Filter and rank articles by relevance."""

from __future__ import annotations

import json
import logging
import re
from html import unescape
from pathlib import Path

from src.config_loader import load_keywords, load_sources
from src.digest_slot import resolve_digest_slot
from src.models import DigestItem, RawArticle

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SEEN_FILE = ROOT / "data" / "seen_urls.json"
SEEN_RETENTION_DAYS = 14

TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(text: str) -> str:
    text = unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def _matches_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(p.lower() in lower for p in patterns)


def _count_matches(text: str, patterns: list[str]) -> int:
    lower = text.lower()
    return sum(1 for p in patterns if p.lower() in lower)


def _score_article(article: RawArticle, text: str, keywords: dict, *, slot: str) -> float:
    score = 0.0

    source_bonus = keywords.get("source_type_bonus", {})
    score += float(source_bonus.get(article.source_type, 0))

    if _matches_any(text, keywords.get("required_any", [])):
        score += 10.0

    score += 5.0 * _count_matches(text, keywords.get("admissions_priority", []))
    score += 2.0 * _count_matches(text, keywords.get("priority_boost", []))
    score -= 4.0 * _count_matches(text, keywords.get("immigration_penalty", []))

    if slot == "morning":
        score += 3.0 * _count_matches(text, keywords.get("morning_slot_boost", []))
    else:
        score += 3.0 * _count_matches(text, keywords.get("evening_slot_boost", []))

    # Immigration-only stories without admissions angle are ranked lower.
    if article.source_type in ("immigration", "policy"):
        if not _matches_any(text, keywords.get("admissions_priority", [])):
            if article.source_type == "immigration":
                score -= 10.0
            elif article.source_type == "policy":
                score -= 3.0

    return score


def _category(source_type: str, text: str) -> str:
    lower = text.lower()
    work_terms = (
        "post-study",
        "post study",
        "graduate route",
        "work permit",
        "work right",
        "opt",
        "psw",
        "pgwp",
        "485",
        "employment after",
        "right to work",
    )
    admissions_terms = (
        "admission",
        "admissions",
        "enrolment",
        "enrollment",
        "intake",
        "tuition",
        "scholarship",
        "entry requirement",
        "application deadline",
        "offer",
    )

    if any(t in lower for t in work_terms):
        return "Post-graduation work rights"
    if source_type == "university" and any(t in lower for t in admissions_terms):
        return "University admissions"
    if source_type in ("policy", "education") and any(t in lower for t in admissions_terms):
        return "Education admissions"
    if source_type == "media" and any(t in lower for t in admissions_terms):
        return "Education admissions"
    if source_type == "university":
        return "University policy"
    if any(t in lower for t in admissions_terms):
        return "Education admissions"
    if source_type in ("policy", "immigration") or "visa" in lower or "immigration" in lower:
        return "Immigration policy"
    return "Education policy"


def _load_seen() -> dict[str, str]:
    if not SEEN_FILE.exists():
        return {}
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_seen(urls: list[str]) -> None:
    from datetime import datetime, timedelta, timezone

    seen = _load_seen()
    now = datetime.now(timezone.utc).isoformat()
    for url in urls:
        seen[url] = now

    cutoff = datetime.now(timezone.utc) - timedelta(days=SEEN_RETENTION_DAYS)
    seen = {
        url: ts
        for url, ts in seen.items()
        if datetime.fromisoformat(ts).replace(tzinfo=timezone.utc) >= cutoff
    }

    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)


def filter_and_rank(articles: list[RawArticle]) -> list[DigestItem]:
    keywords = load_keywords()
    settings = load_sources().get("settings", {})
    max_per_country = settings.get("max_items_per_country", 2)
    max_total = settings.get("max_total_items", 12)
    slot = resolve_digest_slot()

    seen = _load_seen()
    candidates: list[DigestItem] = []

    for article in articles:
        if article.link in seen:
            continue

        text = _clean_text(f"{article.title} {article.summary}")
        if not text:
            continue

        if _matches_any(text, keywords.get("exclude_any", [])):
            continue

        if not _matches_any(text, keywords.get("required_any", [])):
            continue

        if article.source_type == "university" and not _matches_any(
            text, keywords.get("admissions_priority", [])
        ):
            continue

        if article.country_id == "nl" and not _matches_any(
            text, keywords.get("netherlands_extra_any", [])
        ):
            continue

        score = _score_article(article, text, keywords, slot=slot)
        if score <= 0:
            continue

        summary_en = _clean_text(article.summary) or article.title
        if len(summary_en) > 400:
            summary_en = summary_en[:397] + "..."

        candidates.append(
            DigestItem(
                title_en=article.title,
                summary_en=summary_en,
                summary_zh="",
                link=article.link,
                source_name=article.source_name,
                source_type=article.source_type,
                country_id=article.country_id,
                country_name=article.country_name,
                country_flag=article.country_flag,
                category=_category(article.source_type, text),
                score=score,
            )
        )

    candidates.sort(key=lambda x: x.score, reverse=True)

    selected: list[DigestItem] = []
    country_counts: dict[str, int] = {}

    for item in candidates:
        if len(selected) >= max_total:
            break
        count = country_counts.get(item.country_id, 0)
        if count >= max_per_country:
            continue
        selected.append(item)
        country_counts[item.country_id] = count + 1

    logger.info("Selected %d articles after filtering (slot=%s)", len(selected), slot)
    return selected
