"""Bilingual summarization via free LLM APIs with graceful fallback."""

from __future__ import annotations

import json
import logging
import os
import re

import requests

from src.models import DigestItem

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 45


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _fallback_zh(title: str) -> str:
    return f"详情请参阅原文链接：{title}"


def _gemini_summarize(item: DigestItem, api_key: str) -> DigestItem:
    prompt = f"""You are helping study-abroad consultants. Summarize this news item.

Title: {item.title_en}
Source: {item.source_name} ({item.country_name})
Category: {item.category}
Existing text: {_strip_html(item.summary_en)[:800]}

Return ONLY valid JSON with keys:
- summary_en: 1-2 sentence English summary focused on policy impact for international students
- summary_zh: Chinese translation of the summary (简体中文)

News:"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 512},
    }
    response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON in Gemini response")
    data = json.loads(match.group())
    item.summary_en = data.get("summary_en", item.summary_en)[:500]
    item.summary_zh = data.get("summary_zh", _fallback_zh(item.title_en))[:500]
    return item


def _groq_summarize(item: DigestItem, api_key: str) -> DigestItem:
    prompt = f"""Summarize for international education consultants.

Title: {item.title_en}
Source: {item.source_name}
Text: {_strip_html(item.summary_en)[:800]}

Return ONLY JSON: {{"summary_en":"...","summary_zh":"..."}}
summary_en: 1-2 sentences on policy impact for international students.
summary_zh: 简体中文 translation."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 512,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON in Groq response")
    data = json.loads(match.group())
    item.summary_en = data.get("summary_en", item.summary_en)[:500]
    item.summary_zh = data.get("summary_zh", _fallback_zh(item.title_en))[:500]
    return item


def summarize_items(items: list[DigestItem]) -> list[DigestItem]:
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")

    if not api_key:
        logger.warning("No LLM API key; using title-only fallback")
        for item in items:
            if not item.summary_zh:
                item.summary_zh = _fallback_zh(item.title_en)
        return items

    summarized: list[DigestItem] = []
    for item in items:
        try:
            if provider == "groq":
                summarized.append(_groq_summarize(item, api_key))
            else:
                summarized.append(_gemini_summarize(item, api_key))
        except Exception as exc:
            logger.warning("LLM summarize failed for %s: %s", item.link, exc)
            if not item.summary_zh:
                item.summary_zh = _fallback_zh(item.title_en)
            summarized.append(item)

    return summarized
