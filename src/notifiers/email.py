"""HTML email notifications via SMTP."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.models import Digest, DigestItem

logger = logging.getLogger(__name__)


def _item_html(item: DigestItem) -> str:
    type_label = {
        "immigration": "Immigration",
        "university": "University",
        "education": "Education",
    }.get(item.source_type, "News")

    return f"""
    <div style="margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #eee;">
      <h3 style="margin:0 0 8px;color:#1a1a1a;">
        {item.country_flag} {item.country_name} · {item.category}
      </h3>
      <p style="margin:0 0 8px;color:#666;font-size:13px;">
        {item.source_name} ({type_label})
      </p>
      <p style="margin:0 0 6px;"><strong>EN:</strong> {item.summary_en}</p>
      <p style="margin:0 0 6px;"><strong>中:</strong> {item.summary_zh}</p>
      <p style="margin:0;">
        <a href="{item.link}" style="color:#2563eb;">Read original / 阅读原文</a>
      </p>
    </div>
    """


def build_html(digest: Digest) -> str:
    if digest.items:
        body = "".join(_item_html(item) for item in digest.items)
        summary = f"Total: {len(digest.items)} items / 共 {len(digest.items)} 条"
    else:
        body = (
            "<p>No new policy updates matched today's filters.</p>"
            "<p>今日暂无符合筛选条件的新政策动态。</p>"
        )
        summary = "0 items"

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 max-width:640px;margin:0 auto;padding:24px;color:#333;">
      <h1 style="font-size:22px;margin-bottom:4px;">
        🎓 Global Study Policy Daily
      </h1>
      <p style="color:#666;margin-top:0;">{digest.date_label} · {summary}</p>
      {body}
      <p style="font-size:12px;color:#999;margin-top:32px;">
        {digest.disclaimer}<br>{digest.disclaimer_zh}
      </p>
    </body>
    </html>
    """


def send_email(digest: Digest) -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    email_from = os.environ.get("EMAIL_FROM", smtp_user).strip()
    recipients_raw = os.environ.get("EMAIL_RECIPIENTS", "").strip()

    if not all([smtp_host, smtp_user, smtp_password, recipients_raw]):
        logger.warning("SMTP settings incomplete; skipping email")
        return False

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"

    subject = f"🎓 Study Policy Daily {digest.date_label} ({len(digest.items)} items)"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(build_html(digest), "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(email_from, recipients, msg.as_string())

    logger.info("Email sent to %s", recipients)
    return True
