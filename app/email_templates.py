"""Compliant email follow-up templates for physician/dentist disability insurance leads."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import APP_NAME, get_settings
from app.constants import DISCLAIMER


@dataclass(frozen=True)
class EmailTemplate:
    key: str
    name: str
    subject: str
    body: str


def _footer() -> str:
    settings = get_settings()
    return (
        f"\n\n---\n"
        f"{settings.organization_name}\n"
        f"{settings.organization_address}\n\n"
        f"You received this message from {APP_NAME} regarding your disability income insurance inquiry.\n\n"
        f"{DISCLAIMER}\n\n"
        f"To stop receiving emails, reply UNSUBSCRIBE or contact {settings.privacy_contact_email}.\n\n"
        f"Privacy notice: Health and financial information you provide is stored securely. "
        f"Contact {settings.privacy_contact_email} to access, correct, or delete your data."
    )


TEMPLATES: dict[str, EmailTemplate] = {
    "initial_acknowledgment": EmailTemplate(
        key="initial_acknowledgment",
        name="Initial Acknowledgment",
        subject="Your disability insurance inquiry was received",
        body=(
            "Hello Dr. {first_name},\n\n"
            "Thank you for submitting your disability insurance intake form. We received your "
            "information for {specialty} ({career_stage}) at {place_of_work}.\n\n"
            "Next steps:\n"
            "1. A licensed advisor will review your profile within 1 business day.\n"
            "2. We will contact you to discuss coverage options and underwriting considerations.\n"
            "3. If you choose to proceed, Jacob Cornell (NPN 20476670) will guide you through a formal carrier application.\n\n"
            "Please have your income documentation and any existing policy details available for your call."
            + _footer()
        ),
    ),
    "resident_follow_up": EmailTemplate(
        key="resident_follow_up",
        name="Resident / Fellow Follow-Up",
        subject="Disability insurance before you finish training",
        body=(
            "Hello Dr. {first_name},\n\n"
            "As a {career_stage} in {specialty}, you may qualify for resident/fellow disability insurance "
            "programs with simplified underwriting — often without labs or exams.\n\n"
            "Many physicians lock in rates and future increase options before transitioning to attending "
            "income in {work_state}. Would you like a 15-minute overview this week?\n\n"
            "Reply with a good time to connect, or let us know if your timeline has changed."
            + _footer()
        ),
    ),
    "new_attending_urgency": EmailTemplate(
        key="new_attending_urgency",
        name="New Attending — Coverage Gap",
        subject="Protecting your new attending income",
        body=(
            "Hello Dr. {first_name},\n\n"
            "Congratulations on your new role in {specialty} at {place_of_work}. "
            "Group disability coverage through employers often caps benefits and taxes payouts — "
            "leaving a significant income gap for physicians.\n\n"
            "We would like to walk you through individual own-occupation options based on the "
            "information you submitted. Are you available for a brief call in the next few days?"
            + _footer()
        ),
    ),
    "app_ready": EmailTemplate(
        key="app_ready",
        name="Application Ready",
        subject="Your disability insurance application is ready to review",
        body=(
            "Hello Dr. {first_name},\n\n"
            "Based on your intake form, we have prepared a disability insurance application draft "
            "for your review. Please confirm:\n"
            "- Specialty and employer details are correct\n"
            "- Health history is complete and accurate\n"
            "- Desired monthly benefit and income figures\n\n"
            "Accurate disclosures help avoid underwriting delays. We will send a secure link or "
            "schedule a review call at your preference."
            + _footer()
        ),
    ),
    "unsubscribe_confirmation": EmailTemplate(
        key="unsubscribe_confirmation",
        name="Unsubscribe Confirmation",
        subject="You have been unsubscribed",
        body=(
            "Hello Dr. {first_name},\n\n"
            "You will no longer receive follow-up emails regarding your disability insurance inquiry.\n\n"
            "To request deletion of your submitted information, contact {privacy_contact_email}."
            + _footer()
        ),
    ),
}


def render_template(
    template_key: str,
    *,
    first_name: str,
    specialty: str = "",
    career_stage: str = "",
    place_of_work: str = "",
    work_state: str = "",
    custom_message: str | None = None,
) -> EmailTemplate:
    if template_key not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_key}")

    settings = get_settings()
    base = TEMPLATES[template_key]
    context = {
        "first_name": first_name,
        "organization_name": settings.organization_name,
        "specialty": specialty,
        "career_stage": career_stage.replace("_", " "),
        "place_of_work": place_of_work,
        "work_state": work_state,
        "privacy_contact_email": settings.privacy_contact_email,
    }
    body = base.body.format(**context)
    if custom_message:
        body = f"{custom_message.strip()}\n\n{body}"

    return EmailTemplate(
        key=base.key,
        name=base.name,
        subject=base.subject.format(**context),
        body=body,
    )


def list_templates() -> list[EmailTemplate]:
    return list(TEMPLATES.values())