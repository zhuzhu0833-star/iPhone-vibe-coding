"""HTML email notifications via SMTP (Simplified Chinese summaries only)."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.models import Digest
from src.notifiers.html_digest import build_digest_html

logger = logging.getLogger(__name__)


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

    subject = f"🎓 留学政策日报 {digest.date_label}（{len(digest.items)} 条）"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(build_digest_html(digest), "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(email_from, recipients, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail/SMTP login failed. Use an app-specific password, not your login password."
        )
        return False
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return False

    logger.info("Email sent to %s", recipients)
    return True
