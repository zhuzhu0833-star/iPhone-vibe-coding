"""Daily study-abroad policy digest pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from src.digest_store import load_digest_json, save_digest_json
from src.fetcher import fetch_all
from src.filter import filter_and_rank, save_seen
from src.models import Digest
from src.notifiers.email import send_email
from src.notifiers.html_digest import write_digest_html
from src.notifiers.wechat import send_wechat
from src.summarizer import summarize_items

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BEIJING = ZoneInfo("Asia/Shanghai")


def generate_digest() -> Digest:
    now_bj = datetime.now(BEIJING)
    date_label = now_bj.strftime("%Y-%m-%d")
    logger.info("Generating digest for %s (Beijing)", date_label)

    articles = fetch_all()
    items = filter_and_rank(articles)
    items = summarize_items(items)

    digest = Digest(date_label=date_label, items=items)
    write_digest_html(digest)
    save_digest_json(digest)

    if items:
        save_seen([item.link for item in items])

    logger.info("Digest generated: %d items", len(items))
    return digest


def notify_digest(digest: Digest) -> int:
    html_path = write_digest_html(digest)
    wechat_ok = send_wechat(digest, html_path=html_path)
    email_ok = send_email(digest)

    if not wechat_ok and not email_ok:
        logger.error("No notification channel configured or all channels failed")
        return 1

    if not email_ok and wechat_ok:
        logger.warning("Email failed but WeChat succeeded; job marked successful")
    if not wechat_ok and email_ok:
        logger.warning("WeChat failed but email succeeded; job marked successful")

    if len(digest.items) < 3:
        logger.warning(
            "Only %d item(s) in today's digest. Consider enabling more sources "
            "or adding education/immigration feeds in the admin panel.",
            len(digest.items),
        )

    if not digest.items:
        logger.info("No new items today; empty digest sent")

    logger.info(
        "Notifications sent: %d items, wechat=%s, email=%s",
        len(digest.items),
        wechat_ok,
        email_ok,
    )
    return 0


def run(phase: str = "all") -> int:
    if phase == "generate":
        generate_digest()
        return 0

    if phase == "notify":
        return notify_digest(load_digest_json())

    digest = generate_digest()
    return notify_digest(digest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Study abroad policy daily digest")
    parser.add_argument(
        "--phase",
        choices=("all", "generate", "notify"),
        default="all",
        help="generate: fetch+summarize+write HTML; notify: push WeChat/email",
    )
    args = parser.parse_args()
    return run(args.phase)


if __name__ == "__main__":
    sys.exit(main())
