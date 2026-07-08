"""SMTP email alerts for Mutual Income Protection inquiries."""

from __future__ import annotations

import json
import logging
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.config import APP_NAME, BASE_DIR, get_settings
from app.lead_alert_email import build_lead_alert_email

logger = logging.getLogger(__name__)

FAILED_EMAIL_DIR = BASE_DIR / "data" / "failed_emails"
MAX_SEND_ATTEMPTS = 4
RETRY_DELAYS_SEC = (0, 2, 5, 10)


def _smtp_send(*, subject: str, html: str, text: str, to_addr: str) -> None:
    settings = get_settings()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email or settings.smtp_user
    msg["To"] = to_addr
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=45) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.smtp_user, settings.smtp_password.replace(" ", ""))
        server.sendmail(msg["From"], [to_addr], msg.as_string())


def _write_fallback_queue(*, lead_id: int, subject: str, html: str, text: str, error: str) -> Path:
    FAILED_EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = FAILED_EMAIL_DIR / f"lead_{lead_id}_{stamp}.json"
    payload = {
        "lead_id": lead_id,
        "subject": subject,
        "html": html,
        "text": text,
        "error": error,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "app": APP_NAME,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.error("Queued failed email for lead %s at %s: %s", lead_id, path, error)
    return path


def retry_queued_emails(*, limit: int = 20) -> int:
    """Attempt to resend emails from the fallback queue. Returns count sent."""
    settings = get_settings()
    if not settings.smtp_enabled or not settings.alert_email_to:
        return 0

    if not FAILED_EMAIL_DIR.exists():
        return 0

    sent = 0
    for path in sorted(FAILED_EMAIL_DIR.glob("lead_*.json"))[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            _smtp_send(
                subject=payload["subject"],
                html=payload["html"],
                text=payload["text"],
                to_addr=settings.alert_email_to,
            )
            path.unlink(missing_ok=True)
            sent += 1
            logger.info("Resent queued email for lead %s", payload.get("lead_id"))
        except Exception:
            logger.exception("Failed to resend queued email %s", path.name)
    return sent


def send_application_alert(
    *,
    lead_id: int,
    lead_data: dict,
    submitted_at: datetime | None = None,
) -> bool:
    """Send complete lead alert with retries and disk fallback."""
    settings = get_settings()
    to_addr = settings.alert_email_to or "jacobcornell88@gmail.com"

    if not settings.smtp_enabled or not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured; queueing email for lead %s", lead_id)
        subject, html, text = build_lead_alert_email(
            lead_id=lead_id, data=lead_data, submitted_at=submitted_at
        )
        _write_fallback_queue(lead_id=lead_id, subject=subject, html=html, text=text, error="SMTP not configured")
        return False

    subject, html, text = build_lead_alert_email(
        lead_id=lead_id, data=lead_data, submitted_at=submitted_at
    )

    last_error = ""
    for attempt, delay in enumerate(RETRY_DELAYS_SEC[:MAX_SEND_ATTEMPTS], start=1):
        if delay:
            time.sleep(delay)
        try:
            _smtp_send(subject=subject, html=html, text=text, to_addr=to_addr)
            logger.info(
                "Email sent for lead %s to %s (attempt %s/%s)",
                lead_id,
                to_addr,
                attempt,
                MAX_SEND_ATTEMPTS,
            )
            retry_queued_emails(limit=5)
            return True
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Email attempt %s/%s failed for lead %s: %s",
                attempt,
                MAX_SEND_ATTEMPTS,
                lead_id,
                exc,
            )

    _write_fallback_queue(
        lead_id=lead_id,
        subject=subject,
        html=html,
        text=text,
        error=last_error or "max retries exceeded",
    )
    return False


def _build_short_inquiry_email(*, inquiry_id: int, data: dict, submitted_at: datetime | None) -> tuple[str, str, str]:
    import html as html_mod

    name = data.get("full_name") or "Inquiry"
    ts = submitted_at or data.get("created_at")
    ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts or "—")

    hf, hi, wl = data.get("height_feet"), data.get("height_inches"), data.get("weight_lbs")
    height_str = f"{hf}'{hi}\" / {wl} lbs" if hf and wl else "—"

    rows = [
        ("Inquiry ID", f"#{inquiry_id}"),
        ("Submitted", ts_str),
        ("Full Name", data.get("full_name")),
        ("Email", data.get("email")),
        ("Phone", data.get("phone")),
        ("Medical Specialty", data.get("medical_specialty_label") or data.get("medical_specialty")),
        ("Annual Income", data.get("income_range_label") or data.get("income_range")),
        (
            "Disability Insurance",
            data.get("disability_insurance_status_label") or data.get("disability_insurance_status"),
        ),
        ("Best Time to Contact", data.get("best_time_to_contact_label") or data.get("best_time_to_contact")),
        ("Height / Weight", height_str),
        ("BMI", data.get("bmi")),
        ("Tobacco / Nicotine", data.get("tobacco_nicotine_label") or data.get("tobacco_nicotine")),
        ("Medical History", data.get("medical_history")),
        ("Rider Interests", data.get("rider_interests")),
    ]

    def esc(v: object) -> str:
        return html_mod.escape(str(v or "—"), quote=True)

    table_html = "".join(
        f"<tr><td style='padding:10px 14px;border-bottom:1px solid #E8EDF2;font-weight:600;width:40%;'>{esc(k)}</td>"
        f"<td style='padding:10px 14px;border-bottom:1px solid #E8EDF2;'>{esc(v)}</td></tr>"
        for k, v in rows
    )

    subject = f"[{APP_NAME}] New Inquiry — {name}"
    html_body = f"""
    <html><body style="font-family:Segoe UI,Arial,sans-serif;color:#1A2B3C;margin:0;">
    <div style="max-width:600px;margin:0 auto;border:1px solid #D4DCE6;border-radius:10px;overflow:hidden;">
      <div style="background:#002F6C;color:#fff;padding:22px;border-bottom:4px solid #C4A962;">
        <h2 style="margin:0;">{APP_NAME}</h2>
        <p style="margin:8px 0 0;opacity:0.9;">New landing page inquiry — Jake Cornell, NPN 20476670</p>
      </div>
      <div style="padding:22px;">
        <p style="margin:0 0 16px;">A physician or dentist submitted the short lead form.</p>
        <table style="width:100%;border-collapse:collapse;font-size:15px;">{table_html}</table>
      </div>
    </div>
    </body></html>
    """
    text_body = f"{APP_NAME} — New Inquiry #{inquiry_id}\n\n" + "\n".join(f"{k}: {v}" for k, v in rows)
    return subject, html_body, text_body


def send_short_inquiry_alert(
    *,
    inquiry_id: int,
    data: dict,
    submitted_at: datetime | None = None,
) -> bool:
    """Send short-form inquiry alert with retries and fallback."""
    settings = get_settings()
    to_addr = settings.alert_email_to or "jacobcornell88@gmail.com"

    subject, html, text = _build_short_inquiry_email(
        inquiry_id=inquiry_id, data=data, submitted_at=submitted_at
    )

    if not settings.smtp_enabled or not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured; queueing short inquiry %s", inquiry_id)
        _write_fallback_queue(
            lead_id=inquiry_id, subject=subject, html=html, text=text, error="SMTP not configured"
        )
        return False

    last_error = ""
    for attempt, delay in enumerate(RETRY_DELAYS_SEC[:MAX_SEND_ATTEMPTS], start=1):
        if delay:
            time.sleep(delay)
        try:
            _smtp_send(subject=subject, html=html, text=text, to_addr=to_addr)
            logger.info("Short inquiry email sent #%s to %s (attempt %s)", inquiry_id, to_addr, attempt)
            return True
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Short inquiry email attempt %s failed for #%s: %s", attempt, inquiry_id, exc)

    _write_fallback_queue(
        lead_id=inquiry_id, subject=subject, html=html, text=text, error=last_error or "max retries"
    )
    return False