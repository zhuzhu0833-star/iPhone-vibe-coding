"""Fetch articles from RSS feeds."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests

from src.config_loader import load_sources
from src.models import RawArticle

logger = logging.getLogger(__name__)

USER_AGENT = (
    "StudyAbroadDigestBot/1.0 (+https://github.com; educational policy aggregator)"
)
REQUEST_TIMEOUT = 20


def _parse_published(entry: dict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (TypeError, ValueError):
                pass
    return None


def _entry_summary(entry: dict) -> str:
    for key in ("summary", "description", "content"):
        value = entry.get(key)
        if isinstance(value, list) and value:
            value = value[0].get("value", "")
        if value:
            return str(value)
    return ""


def fetch_all() -> list[RawArticle]:
    config = load_sources()
    lookback_hours = config.get("settings", {}).get("lookback_hours", 36)
    max_per_source = config.get("settings", {}).get("max_items_per_source", 5)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    articles: list[RawArticle] = []

    for country in config.get("countries", []):
        for source in country.get("sources", []):
            url = source.get("url")
            if not url:
                continue
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
            except Exception as exc:
                logger.warning(
                    "Failed to fetch %s (%s): %s",
                    source.get("name"),
                    url,
                    exc,
                )
                continue

            count = 0
            for entry in feed.entries:
                if count >= max_per_source:
                    break

                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                if not title or not link:
                    continue

                published = _parse_published(entry)
                if not published:
                    continue
                if published < cutoff:
                    continue

                articles.append(
                    RawArticle(
                        title=title,
                        link=link,
                        summary=_entry_summary(entry),
                        published=published,
                        source_name=source.get("name", "Unknown"),
                        source_type=source.get("type", "general"),
                        country_id=country.get("id", ""),
                        country_name=country.get("name", ""),
                        country_flag=country.get("flag", ""),
                    )
                )
                count += 1

    logger.info("Fetched %d raw articles", len(articles))
    return articles
