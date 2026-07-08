"""SMTP email alerts for Mutual Income Protection inquiries."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import APP_NAME, get_settings
from app.constants import AGENT_CREDENTIAL_LINE

logger = logging.getLogger(__name__)


def _build_application_email(*, lead_id: int, summary: dict) -> tuple[str, str, str]:
    subject = f"[{APP_NAME}] New Inquiry #{lead_id} — {summary.get('full_name', 'Applicant')}"
    pref = summary.get("contact_preference", "either")
    html = f"""
    <html><body style="font-family:Segoe UI,Arial,sans-serif;color:#1A2B3C;">
    <div style="max-width:640px;margin:0 auto;border:1px solid #D4DCE6;border-radius:8px;overflow:hidden;">
      <div style="background:#002F6C;color:#fff;padding:20px;border-bottom:4px solid #C4A962;">
        <h2 style="margin:0;">{APP_NAME}</h2>
        <p style="margin:8px 0 0;opacity:0.9;">New information-gathering inquiry — {AGENT_CREDENTIAL_LINE}</p>
      </div>
      <div style="padding:20px;">
        <p><strong>Inquiry ID:</strong> {lead_id}</p>
        <p><strong>Name:</strong> {summary.get('full_name')}</p>
        <p><strong>Email:</strong> {summary.get('email')}</p>
        <p><strong>Phone:</strong> {summary.get('phone')}</p>
        <p><strong>Contact preference:</strong> {pref}</p>
        <p><strong>Occupation:</strong> {summary.get('occupation_title')} — {summary.get('specialty')}</p>
        <p><strong>Employer:</strong> {summary.get('place_of_work')}</p>
        <p><strong>Annual Income:</strong> ${summary.get('annual_income_amount', 0):,}</p>
        <p><strong>AI Score:</strong> {summary.get('score')} ({summary.get('score_tier')})</p>
        <p><strong>Reason:</strong><br>{summary.get('reason_for_applying', '—')}</p>
        <hr>
        <p style="font-size:12px;color:#5A6B7D;">
          {AGENT_CREDENTIAL_LINE} Follow up per applicant's contact preference.
          SSN and payment details to be collected by agent during formal application.
        </p>
      </div>
    </div>
    </body></html>
    """
    text = (
        f"{APP_NAME} — Inquiry #{lead_id}\n"
        f"Name: {summary.get('full_name')}\n"
        f"Contact via: {pref}\n"
        f"Score: {summary.get('score')} ({summary.get('score_tier')})\n"
    )
    return subject, html, text


def send_application_alert(*, lead_id: int, summary: dict) -> bool:
    settings = get_settings()
    if not settings.smtp_enabled or not settings.smtp_user or not settings.alert_email_to:
        logger.warning("SMTP not configured; skipping email for inquiry %s", lead_id)
        return False

    subject, html, text = _build_application_email(lead_id=lead_id, summary=summary)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email or settings.smtp_user
    msg["To"] = settings.alert_email_to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password.replace(" ", ""))
            server.sendmail(msg["From"], [settings.alert_email_to], msg.as_string())
        return True
    except Exception:
        logger.exception("Failed to send email for inquiry %s", lead_id)
        return False