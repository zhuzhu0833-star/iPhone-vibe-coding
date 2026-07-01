"""WeChat Work (企业微信) group bot notifications via webhook."""

from __future__ import annotations

import logging
import os

import requests

from src.models import Digest, DigestItem

logger = logging.getLogger(__name__)

# WeChat Work markdown messages are limited to 4096 bytes.
MAX_MARKDOWN_BYTES = 3800


def _type_label(source_type: str) -> str:
    return {
        "immigration": "Immigration",
        "university": "University",
        "education": "Education",
    }.get(source_type, "News")


def _item_markdown(item: DigestItem, index: int) -> str:
    label = _type_label(item.source_type)
    return (
        f"### {index}. {item.country_flag} {item.country_name} · {item.category}\n"
        f"> {item.source_name} ({label})\n\n"
        f"**EN** {item.summary_en}\n\n"
        f"**中** {item.summary_zh}\n\n"
        f"[阅读原文]({item.link})\n"
    )


def build_markdown_messages(digest: Digest) -> list[str]:
    header = f"## 🎓 全球留学政策日报 | {digest.date_label}\n"

    if not digest.items:
        body = (
            "今日暂无符合筛选条件的新政策动态。\n"
            "No new policy updates matched today's filters."
        )
        return [header + body]

    footer = (
        f"\n---\n"
        f"共 **{len(digest.items)}** 条 · {digest.disclaimer_zh}\n"
        f"{digest.disclaimer}"
    )

    messages: list[str] = []
    current = header

    for i, item in enumerate(digest.items, start=1):
        block = _item_markdown(item, i)
        candidate = current + block
        if len(candidate.encode("utf-8")) > MAX_MARKDOWN_BYTES and current != header:
            messages.append(current.rstrip())
            current = f"## 🎓 全球留学政策日报（续）| {digest.date_label}\n" + block
        else:
            current = candidate

    current += footer
    if len(current.encode("utf-8")) > MAX_MARKDOWN_BYTES:
        messages.append(current[: MAX_MARKDOWN_BYTES // 2])
        messages.append(current[MAX_MARKDOWN_BYTES // 2 :])
    else:
        messages.append(current)

    return messages


def _send_markdown(webhook: str, content: str) -> None:
    response = requests.post(
        webhook,
        json={"msgtype": "markdown", "markdown": {"content": content}},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"WeChat Work API error: {data}")


def send_wechat(digest: Digest) -> bool:
    webhook = os.environ.get("WECHAT_WORK_WEBHOOK_URL", "").strip()
    if not webhook:
        logger.warning("WECHAT_WORK_WEBHOOK_URL not set; skipping WeChat Work")
        return False

    messages = build_markdown_messages(digest)
    for i, content in enumerate(messages, start=1):
        _send_markdown(webhook, content)
        logger.info("WeChat Work message %d/%d sent", i, len(messages))

    return True
