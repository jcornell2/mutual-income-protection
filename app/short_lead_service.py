"""Business logic for short-form landing page inquiries."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.email_service import send_short_inquiry_alert
from app.models import LeadStatus, ShortLead
from app.privacy import decrypt_field, encrypt_field, hash_identifier, log_audit
from app.schemas import ShortLeadCreate, ShortLeadResponse

LABELS = {
    "medical_specialty": {
        "physician": "Physician",
        "dentist": "Dentist",
        "surgeon": "Surgeon",
        "other": "Other",
    },
    "income_range": {
        "200_400k": "$200k–$400k",
        "400_600k": "$400k–$600k",
        "600k_plus": "$600k+",
        "prefer_not_to_say": "Prefer not to say",
    },
    "disability_insurance_status": {
        "none": "No disability insurance",
        "employer_group_only": "Employer group coverage only",
        "individual_policy": "Individual policy",
        "group_and_individual": "Both group and individual",
        "unsure": "Unsure / exploring options",
    },
    "best_time_to_contact": {
        "morning": "Morning (8am–12pm)",
        "afternoon": "Afternoon (12pm–5pm)",
        "evening": "Evening (5pm–8pm)",
        "anytime": "Anytime",
        "weekends": "Weekends only",
    },
    "tobacco_nicotine": {
        "never": "Never",
        "former": "Former user",
        "current": "Current user",
    },
}


def _label(group: str, key: str) -> str:
    return LABELS.get(group, {}).get(key, key.replace("_", " ").title())


def _calc_bmi(height_feet: int | None, height_inches: int | None, weight_lbs: int | None) -> float | None:
    if not height_feet or weight_lbs is None:
        return None
    total_inches = height_feet * 12 + (height_inches or 0)
    if total_inches <= 0:
        return None
    return round((weight_lbs / (total_inches**2)) * 703, 1)


def short_lead_to_response(lead: ShortLead) -> ShortLeadResponse:
    return ShortLeadResponse(
        id=lead.id,
        full_name=decrypt_field(lead.full_name_enc) or "",
        email=decrypt_field(lead.email_enc) or "",
        phone=decrypt_field(lead.phone_enc) or "",
        medical_specialty=lead.medical_specialty,
        income_range=lead.income_range,
        disability_insurance_status=lead.disability_insurance_status,
        best_time_to_contact=lead.best_time_to_contact,
        height_feet=lead.height_feet,
        height_inches=lead.height_inches,
        weight_lbs=lead.weight_lbs,
        bmi=_calc_bmi(lead.height_feet, lead.height_inches, lead.weight_lbs),
        tobacco_nicotine=lead.tobacco_nicotine,
        medical_history=decrypt_field(lead.medical_history_enc),
        interest_future_income_option=lead.interest_future_income_option,
        interest_cola=lead.interest_cola,
        interest_extended_partial=lead.interest_extended_partial,
        status=lead.status,
        email_sent=lead.email_sent,
        created_at=lead.created_at,
    )


def short_lead_to_email_data(lead: ShortLead) -> dict:
    data = short_lead_to_response(lead).model_dump()
    data["medical_specialty_label"] = _label("medical_specialty", lead.medical_specialty)
    data["income_range_label"] = _label("income_range", lead.income_range)
    data["disability_insurance_status_label"] = _label(
        "disability_insurance_status", lead.disability_insurance_status
    )
    data["best_time_to_contact_label"] = _label("best_time_to_contact", lead.best_time_to_contact)
    data["tobacco_nicotine_label"] = _label("tobacco_nicotine", lead.tobacco_nicotine or "")
    riders = []
    if lead.interest_future_income_option:
        riders.append("Future Income Option")
    if lead.interest_cola:
        riders.append("COLA")
    if lead.interest_extended_partial:
        riders.append("Extended Partial")
    data["rider_interests"] = ", ".join(riders) if riders else "None selected"
    return data


def create_short_lead(db: Session, payload: ShortLeadCreate, *, actor: str = "landing") -> ShortLead:
    email_hash = hash_identifier(payload.email)
    if db.query(ShortLead).filter(
        ShortLead.email_hash == email_hash,
        ShortLead.status != LeadStatus.UNSUBSCRIBED.value,
    ).first():
        raise ValueError("We already have your information on file. Jacob will be in touch soon.")

    lead = ShortLead(
        full_name_enc=encrypt_field(payload.full_name),
        email_enc=encrypt_field(payload.email),
        phone_enc=encrypt_field(payload.phone),
        email_hash=email_hash,
        medical_specialty=payload.medical_specialty,
        income_range=payload.income_range,
        disability_insurance_status=payload.disability_insurance_status,
        best_time_to_contact=payload.best_time_to_contact,
        height_feet=payload.height_feet,
        height_inches=payload.height_inches,
        weight_lbs=payload.weight_lbs,
        tobacco_nicotine=payload.tobacco_nicotine,
        medical_history_enc=encrypt_field(payload.medical_history),
        interest_future_income_option=payload.interest_future_income_option,
        interest_cola=payload.interest_cola,
        interest_extended_partial=payload.interest_extended_partial,
        status=LeadStatus.NEW.value,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    email_data = short_lead_to_email_data(lead)
    email_ok = send_short_inquiry_alert(
        inquiry_id=lead.id,
        data=email_data,
        submitted_at=lead.created_at,
    )
    if email_ok:
        lead.email_sent = True
        db.commit()
        db.refresh(lead)

    log_audit(
        db,
        action="create",
        entity_type="short_inquiry",
        entity_id=lead.id,
        actor=actor,
        details=(
            f"specialty={payload.medical_specialty} income={payload.income_range} "
            f"bmi={email_data.get('bmi')} riders={email_data.get('rider_interests')} email_sent={email_ok}"
        ),
    )
    return lead


def list_short_leads(db: Session, *, limit: int = 500) -> list[ShortLead]:
    return db.query(ShortLead).order_by(ShortLead.created_at.desc()).limit(limit).all()