"""Daily study-abroad policy digest pipeline."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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


def run() -> int:
    now_bj = datetime.now(BEIJING)
    date_label = now_bj.strftime("%Y-%m-%d")

    logger.info("Starting digest for %s (Beijing)", date_label)

    articles = fetch_all()
    items = filter_and_rank(articles)
    items = summarize_items(items)

    digest = Digest(date_label=date_label, items=items)
    html_path = write_digest_html(digest)

    wechat_ok = send_wechat(digest, html_path=html_path)
    email_ok = send_email(digest)

    if items:
        save_seen([item.link for item in items])

    if not wechat_ok and not email_ok:
        logger.error("No notification channel configured or all channels failed")
        return 1

    if not email_ok and wechat_ok:
        logger.warning("Email failed but WeChat succeeded; job marked successful")
    if not wechat_ok and email_ok:
        logger.warning("WeChat failed but email succeeded; job marked successful")

    if len(items) < 3:
        logger.warning(
            "Only %d item(s) in today's digest. Consider enabling more sources "
            "or adding education/immigration feeds in the admin panel.",
            len(items),
        )

    # Still send an empty digest when no items matched (team sees "no updates today").
    if not items:
        logger.info("No new items today; empty digest sent")

    logger.info(
        "Digest complete: %d items, wechat=%s, email=%s",
        len(items),
        wechat_ok,
        email_ok,
    )
    return 0


if __name__ == "__main__":
    sys.exit(run())
