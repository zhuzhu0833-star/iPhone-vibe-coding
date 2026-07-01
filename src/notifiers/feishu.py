"""Feishu (Lark) interactive card notifications."""

from __future__ import annotations

import logging
import os

import requests

from src.models import Digest, DigestItem

logger = logging.getLogger(__name__)


def _item_block(item: DigestItem, index: int) -> dict:
    type_label = {
        "immigration": "Immigration",
        "university": "University",
        "education": "Education",
    }.get(item.source_type, "News")

    text = (
        f"**{index}. {item.country_flag} {item.country_name} · {item.category}**\n"
        f"*{item.source_name} ({type_label})*\n\n"
        f"**EN** {item.summary_en}\n\n"
        f"**中** {item.summary_zh}\n\n"
        f"[Read original / 阅读原文]({item.link})"
    )
    return {
        "tag": "div",
        "text": {"tag": "lark_md", "content": text},
    }


def build_card(digest: Digest) -> dict:
    header_title = f"🎓 Global Study Policy Daily | {digest.date_label}"
    if not digest.items:
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        "No new policy updates matched today's filters.\n"
                        "今日暂无符合筛选条件的新政策动态。"
                    ),
                },
            }
        ]
    else:
        elements = [_item_block(item, i + 1) for i, item in enumerate(digest.items)]
        elements.append({"tag": "hr"})
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**Total / 共 {len(digest.items)} items**\n"
                        f"_{digest.disclaimer}_\n"
                        f"_{digest.disclaimer_zh}_"
                    ),
                },
            }
        )

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": header_title},
                "template": "blue",
            },
            "elements": elements,
        },
    }


def send_feishu(digest: Digest) -> bool:
    webhook = os.environ.get("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook:
        logger.warning("FEISHU_WEBHOOK_URL not set; skipping Feishu")
        return False

    payload = build_card(digest)
    response = requests.post(webhook, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if data.get("code") not in (0, None):
        raise RuntimeError(f"Feishu API error: {data}")
    logger.info("Feishu notification sent")
    return True
