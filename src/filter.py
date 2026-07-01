"""Filter and rank articles by relevance."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from html import unescape
from pathlib import Path

from src.config_loader import load_keywords, load_sources
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


def _score_article(text: str, keywords: dict) -> float:
    score = 0.0
    if _matches_any(text, keywords.get("required_any", [])):
        score += 10.0
    for term in keywords.get("priority_boost", []):
        if term.lower() in text.lower():
            score += 2.0
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
    if any(t in lower for t in work_terms):
        return "Post-graduation work rights"
    if source_type == "immigration" or "visa" in lower or "immigration" in lower:
        return "Immigration policy"
    if source_type == "university":
        return "University policy"
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

        if article.source_type == "immigration":
            score = 15.0 + _score_article(text, keywords)
        else:
            if not _matches_any(text, keywords.get("required_any", [])):
                continue
            score = _score_article(text, keywords)

        if article.country_id == "nl" and not _matches_any(
            text, keywords.get("netherlands_extra_any", [])
        ):
            continue

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

    logger.info("Selected %d articles after filtering", len(selected))
    return selected
