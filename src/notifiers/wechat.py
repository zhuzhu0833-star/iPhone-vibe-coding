"""WeChat Work (企业微信) group bot — push single-page HTML digest file."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from src.models import Digest
from src.notifiers.html_digest import write_digest_html

logger = logging.getLogger(__name__)


def _webhook_key(webhook: str) -> str:
    key = parse_qs(urlparse(webhook).query).get("key", [""])[0]
    if not key:
        raise ValueError("Invalid WeChat Work webhook URL: missing key")
    return key


def _upload_file(webhook: str, file_path: Path) -> str:
    key = _webhook_key(webhook)
    upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={key}&type=file"
    with open(file_path, "rb") as handle:
        response = requests.post(
            upload_url,
            files={"media": (file_path.name, handle, "text/html")},
            timeout=30,
        )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"WeChat file upload failed: {data}")
    media_id = data.get("media_id")
    if not media_id:
        raise RuntimeError(f"No media_id in upload response: {data}")
    return media_id


def _send_file(webhook: str, media_id: str) -> None:
    response = requests.post(
        webhook,
        json={"msgtype": "file", "file": {"media_id": media_id}},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"WeChat Work API error: {data}")


def _send_text(webhook: str, content: str) -> None:
    response = requests.post(
        webhook,
        json={"msgtype": "text", "text": {"content": content}},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"WeChat Work API error: {data}")


def send_wechat(digest: Digest, *, html_path: Path | None = None) -> bool:
    webhook = os.environ.get("WECHAT_WORK_WEBHOOK_URL", "").strip()
    if not webhook:
        logger.warning("WECHAT_WORK_WEBHOOK_URL not set; skipping WeChat Work")
        return False

    upload_path: Path | None = None
    try:
        if html_path is None:
            html_path = write_digest_html(digest)

        count = len(digest.items)
        intro = (
            f"🎓 全球留学政策日报 · {digest.slot_label_zh} {digest.date_label}\n"
            f"共 {count} 条 · {digest.slot_focus_zh}\n"
            f"中文摘要见下方 HTML 文件，点击即可打开阅读。"
        )
        _send_text(webhook, intro)

        upload_dir = Path(tempfile.mkdtemp(prefix="digest-upload-"))
        upload_path = upload_dir / f"留学政策日报-{digest.date_label}-{digest.slot_label_zh}.html"
        shutil.copy(html_path, upload_path)

        media_id = _upload_file(webhook, upload_path)
        _send_file(webhook, media_id)
        logger.info("WeChat Work HTML digest sent (%d items)", count)

        public_base = os.environ.get("DIGEST_PUBLIC_URL", "").strip().rstrip("/")
        if public_base:
            page_url = f"{public_base}/digest/latest-{digest.slot}.html"
            _send_text(webhook, f"📎 在线阅读：{page_url}")
            logger.info("WeChat Work page link sent: %s", page_url)

        return True
    except Exception as exc:
        logger.error("WeChat Work send failed: %s", exc)
        return False
    finally:
        if upload_path is not None:
            shutil.rmtree(upload_path.parent, ignore_errors=True)
