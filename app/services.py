"""Business logic for Mutual Income Protection applications."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.email_service import send_application_alert
from app.email_templates import render_template
from app.models import FollowUp, Lead, LeadStatus
from app.privacy import decrypt_field, encrypt_field, hash_identifier, log_audit
from app.schemas import DashboardStats, LeadCreate, LeadResponse, LeadSummary, LeadUpdate
from app.scoring import _income_range_from_amount, calculate_score


def _first_name(full_name: str) -> str:
    return full_name.strip().split()[0] if full_name.strip() else "there"


def _calc_bmi(height_feet: int, height_inches: int, weight_lbs: int) -> float | None:
    total_inches = height_feet * 12 + height_inches
    if total_inches <= 0:
        return None
    return round((weight_lbs / (total_inches**2)) * 703, 1)


def _format_conditions(conditions: list[str], other: str | None) -> str:
    items = [c for c in conditions if c and c != "None reported"]
    if other:
        items.append(other.strip())
    return "; ".join(items) if items else "None reported"


def _parse_breakdown(lead: Lead) -> dict[str, int] | None:
    if not lead.score_breakdown_json:
        return None
    try:
        return json.loads(lead.score_breakdown_json)
    except json.JSONDecodeError:
        return None


def _enc(value: str | None) -> str | None:
    return encrypt_field(value) if value else None


def lead_to_response(lead: Lead) -> LeadResponse:
    return LeadResponse(
        id=lead.id,
        full_name=decrypt_field(lead.full_name_enc) or "",
        email=decrypt_field(lead.email_enc) or "",
        phone=decrypt_field(lead.phone_enc) or "",
        date_of_birth=decrypt_field(lead.dob_enc) or "",
        contact_preference=lead.contact_preference,
        address_street=decrypt_field(lead.address_street_enc) or "",
        address_line2=decrypt_field(lead.address_line2_enc),
        address_city=lead.address_city,
        address_state=lead.address_state,
        address_zip=lead.address_zip,
        marital_status=lead.marital_status,
        dependents_count=lead.dependents_count,
        dependents_details=decrypt_field(lead.dependents_details_enc),
        gender=lead.gender,
        provider_type=lead.provider_type,
        career_stage=lead.career_stage,
        specialty=lead.specialty,
        occupation_title=lead.occupation_title,
        place_of_work=lead.place_of_work,
        employer_type=lead.employer_type,
        duties_performed=decrypt_field(lead.duties_performed_enc),
        hours_worked_per_week=lead.hours_worked_per_week,
        income_sources=decrypt_field(lead.income_sources_enc),
        key_responsibilities=decrypt_field(lead.key_responsibilities_enc),
        specialized_skills=decrypt_field(lead.specialized_skills_enc),
        occupation_details=decrypt_field(lead.occupation_details_enc),
        training_program=lead.training_program,
        work_city=lead.work_city,
        work_state=lead.work_state,
        work_zip=lead.work_zip,
        license_state=lead.license_state,
        graduation_year=lead.graduation_year,
        years_in_practice=lead.years_in_practice,
        annual_income_amount=lead.annual_income_amount,
        annual_income_range=lead.annual_income_range,
        income_breakdown=decrypt_field(lead.income_breakdown_enc),
        monthly_expenses_range=lead.monthly_expenses_range,
        monthly_expenses_detail=decrypt_field(lead.monthly_expenses_detail_enc),
        home_value_range=lead.home_value_range,
        vehicles_value_range=lead.vehicles_value_range,
        major_assets=decrypt_field(lead.major_assets_enc),
        debts_loans=decrypt_field(lead.debts_loans_enc),
        height_feet=lead.height_feet,
        height_inches=lead.height_inches,
        weight_lbs=lead.weight_lbs,
        bmi=_calc_bmi(lead.height_feet, lead.height_inches, lead.weight_lbs),
        medical_conditions=decrypt_field(lead.medical_conditions_enc),
        medications=decrypt_field(lead.medications_enc),
        surgeries=decrypt_field(lead.surgeries_enc),
        family_medical_history=decrypt_field(lead.family_medical_history_enc),
        exercise_frequency=lead.exercise_frequency,
        hobbies_activities=decrypt_field(lead.hobbies_activities_enc),
        travel_frequency=lead.travel_frequency,
        dangerous_activities=decrypt_field(lead.dangerous_activities_enc),
        tobacco_nicotine=lead.tobacco_nicotine,
        cannabis_use=lead.cannabis_use,
        alcohol_use=lead.alcohol_use,
        drug_use=lead.drug_use,
        dui_history=lead.dui_history,
        military_status=lead.military_status,
        current_disability_status=lead.current_disability_status,
        current_disability_details=decrypt_field(lead.current_disability_details_enc),
        health_insurance_status=lead.health_insurance_status,
        prior_application_denied=lead.prior_application_denied,
        prior_applications_denials=decrypt_field(lead.prior_applications_denials_enc),
        insurance_history=decrypt_field(lead.insurance_history_enc),
        existing_disability_insurance=lead.existing_disability_insurance,
        existing_life_insurance=lead.existing_life_insurance,
        existing_policies=decrypt_field(lead.existing_policies_enc),
        group_coverage_through_employer=lead.group_coverage_through_employer,
        beneficiary_info=decrypt_field(lead.beneficiary_info_enc),
        assets_range=lead.assets_range,
        student_loans_range=lead.student_loans_range,
        desired_monthly_benefit=lead.desired_monthly_benefit,
        reason_for_applying=decrypt_field(lead.reason_for_applying_enc),
        current_symptoms=decrypt_field(lead.current_symptoms_enc),
        work_impact=decrypt_field(lead.work_impact_enc),
        referral_source=lead.referral_source,
        status=lead.status,
        score=lead.score,
        score_tier=lead.score_tier,
        score_breakdown=_parse_breakdown(lead),
        email_sent=lead.email_sent,
        privacy_consent=lead.privacy_consent,
        medical_exam_acknowledgment=lead.medical_exam_acknowledgment,
        agent_followup_acknowledgment=lead.agent_followup_acknowledgment,
        premium_target_acknowledgment=lead.premium_target_acknowledgment,
        consent_timestamp=lead.consent_timestamp,
        notes=decrypt_field(lead.notes_enc),
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        contacted_at=lead.contacted_at,
        converted_at=lead.converted_at,
    )


def lead_to_summary(lead: Lead) -> LeadSummary:
    return LeadSummary(
        id=lead.id,
        full_name=decrypt_field(lead.full_name_enc) or "",
        email=decrypt_field(lead.email_enc) or "",
        contact_preference=lead.contact_preference,
        provider_type=lead.provider_type,
        career_stage=lead.career_stage,
        specialty=lead.specialty,
        occupation_title=lead.occupation_title,
        place_of_work=lead.place_of_work,
        address_state=lead.address_state,
        annual_income_amount=lead.annual_income_amount,
        current_disability_status=lead.current_disability_status,
        status=lead.status,
        score=lead.score,
        score_tier=lead.score_tier,
        email_sent=lead.email_sent,
        created_at=lead.created_at,
    )


def create_lead(db: Session, payload: LeadCreate, *, actor: str = "public", ip: str | None = None) -> Lead:
    email_hash = hash_identifier(payload.email)
    if db.query(Lead).filter(Lead.email_hash == email_hash, Lead.status != LeadStatus.UNSUBSCRIBED.value).first():
        raise ValueError("An inquiry with this email already exists.")

    conditions_text = _format_conditions(payload.medical_conditions, payload.medical_conditions_other)
    score_data = payload.model_dump(mode="json")
    score_data["medical_conditions_text"] = conditions_text
    score_result = calculate_score(score_data)
    income_range = _income_range_from_amount(payload.annual_income_amount)
    now = datetime.now(timezone.utc)

    lead = Lead(
        full_name_enc=encrypt_field(payload.full_name),
        email_enc=encrypt_field(payload.email),
        phone_enc=encrypt_field(payload.phone),
        dob_enc=encrypt_field(payload.date_of_birth.isoformat()),
        ssn_enc=None,
        ssn_hash=None,
        contact_preference=payload.contact_preference,
        address_street_enc=encrypt_field(payload.address_street),
        address_line2_enc=_enc(payload.address_line2),
        address_city=payload.address_city,
        address_state=payload.address_state,
        address_zip=payload.address_zip,
        email_hash=email_hash,
        marital_status=payload.marital_status,
        dependents_count=payload.dependents_count,
        dependents_details_enc=_enc(payload.dependents_details),
        gender=payload.gender,
        provider_type=payload.provider_type.value,
        career_stage=payload.career_stage.value,
        specialty=payload.specialty,
        occupation_title=payload.occupation_title,
        place_of_work=payload.place_of_work,
        employer_type=payload.employer_type,
        duties_performed_enc=encrypt_field(payload.duties_performed),
        hours_worked_per_week=payload.hours_worked_per_week,
        income_sources_enc=encrypt_field(payload.income_sources),
        key_responsibilities_enc=encrypt_field(payload.key_responsibilities),
        specialized_skills_enc=_enc(payload.specialized_skills),
        occupation_details_enc=_enc(payload.occupation_details),
        training_program=payload.training_program,
        work_city=payload.work_city,
        work_state=payload.work_state,
        work_zip=payload.work_zip,
        license_state=payload.license_state,
        graduation_year=payload.graduation_year,
        years_in_practice=payload.years_in_practice,
        annual_income_amount=payload.annual_income_amount,
        annual_income_range=income_range,
        income_breakdown_enc=encrypt_field(payload.income_breakdown),
        monthly_expenses_range=payload.monthly_expenses_range,
        monthly_expenses_detail_enc=_enc(payload.monthly_expenses_detail),
        home_value_range=payload.home_value_range,
        vehicles_value_range=payload.vehicles_value_range,
        major_assets_enc=_enc(payload.major_assets),
        debts_loans_enc=encrypt_field(payload.debts_loans),
        height_feet=payload.height_feet,
        height_inches=payload.height_inches,
        weight_lbs=payload.weight_lbs,
        medical_conditions_enc=encrypt_field(conditions_text),
        medications_enc=_enc(payload.medications),
        surgeries_enc=_enc(payload.surgeries),
        family_medical_history_enc=_enc(payload.family_medical_history),
        exercise_frequency=payload.exercise_frequency,
        hobbies_activities_enc=_enc(payload.hobbies_activities),
        travel_frequency=payload.travel_frequency,
        dangerous_activities_enc=_enc(payload.dangerous_activities),
        tobacco_nicotine=payload.tobacco_nicotine,
        cannabis_use=payload.cannabis_use,
        alcohol_use=payload.alcohol_use,
        drug_use=payload.drug_use,
        dui_history=payload.dui_history,
        military_status=payload.military_status,
        current_disability_status=payload.current_disability_status,
        current_disability_details_enc=_enc(payload.current_disability_details),
        health_insurance_status=payload.health_insurance_status,
        prior_application_denied=payload.prior_application_denied,
        prior_applications_denials_enc=_enc(payload.prior_applications_denials),
        insurance_history_enc=_enc(payload.insurance_history),
        existing_disability_insurance=payload.existing_disability_insurance,
        existing_life_insurance=payload.existing_life_insurance,
        existing_policies_enc=_enc(payload.existing_policies),
        group_coverage_through_employer=payload.group_coverage_through_employer,
        beneficiary_info_enc=_enc(payload.beneficiary_info),
        assets_range=payload.assets_range,
        student_loans_range=payload.student_loans_range,
        desired_monthly_benefit=payload.desired_monthly_benefit,
        reason_for_applying_enc=encrypt_field(payload.reason_for_applying),
        current_symptoms_enc=_enc(payload.current_symptoms),
        work_impact_enc=_enc(payload.work_impact),
        referral_source=payload.referral_source,
        notes_enc=_enc(payload.notes),
        privacy_consent=payload.privacy_consent,
        medical_exam_acknowledgment=payload.medical_exam_acknowledgment,
        agent_followup_acknowledgment=payload.agent_followup_acknowledgment,
        premium_target_acknowledgment=payload.premium_target_acknowledgment,
        consent_timestamp=now,
        score=score_result.score,
        score_tier=score_result.tier,
        score_breakdown_json=json.dumps(score_result.breakdown),
        status=LeadStatus.NEW.value,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    response = lead_to_response(lead)
    email_ok = send_application_alert(
        lead_id=lead.id,
        summary={
            "full_name": response.full_name,
            "email": response.email,
            "phone": response.phone,
            "contact_preference": response.contact_preference,
            "occupation_title": response.occupation_title,
            "specialty": response.specialty,
            "place_of_work": response.place_of_work,
            "career_stage": response.career_stage,
            "annual_income_amount": response.annual_income_amount,
            "score": response.score,
            "score_tier": response.score_tier,
            "reason_for_applying": response.reason_for_applying,
        },
    )
    if email_ok:
        lead.email_sent = True
        db.commit()
        db.refresh(lead)

    log_audit(
        db,
        action="create",
        entity_type="application",
        entity_id=lead.id,
        actor=actor,
        details=f"Mutual Income Protection app tier={score_result.tier} score={score_result.score} email_sent={email_ok}",
        ip_address=ip,
    )
    return lead


def list_leads(db: Session, *, status: str | None = None, tier: str | None = None,
               provider_type: str | None = None, career_stage: str | None = None, limit: int = 500) -> list[Lead]:
    query = db.query(Lead).order_by(Lead.created_at.desc())
    if status:
        query = query.filter(Lead.status == status)
    if tier:
        query = query.filter(Lead.score_tier == tier)
    if provider_type:
        query = query.filter(Lead.provider_type == provider_type)
    if career_stage:
        query = query.filter(Lead.career_stage == career_stage)
    return query.limit(limit).all()


def get_lead(db: Session, lead_id: int) -> Lead | None:
    return db.query(Lead).filter(Lead.id == lead_id).first()


def update_lead(db: Session, lead: Lead, payload: LeadUpdate, *, actor: str = "admin", ip: str | None = None) -> Lead:
    if payload.status is not None:
        lead.status = payload.status
        now = datetime.now(timezone.utc)
        if payload.status == LeadStatus.CONTACTED.value and not lead.contacted_at:
            lead.contacted_at = now
        if payload.status in (LeadStatus.CONVERTED.value, LeadStatus.APP_SUBMITTED.value) and not lead.converted_at:
            lead.converted_at = now
    if payload.notes is not None:
        lead.notes_enc = encrypt_field(payload.notes)
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    log_audit(db, action="update", entity_type="application", entity_id=lead.id, actor=actor,
              details=f"status={lead.status}", ip_address=ip)
    return lead


def delete_lead(db: Session, lead: Lead, *, actor: str = "admin", ip: str | None = None) -> None:
    lid = lead.id
    db.delete(lead)
    db.commit()
    log_audit(db, action="delete", entity_type="application", entity_id=lid, actor=actor,
              details="Application erased", ip_address=ip)


def get_dashboard_stats(db: Session) -> DashboardStats:
    total = db.query(func.count(Lead.id)).scalar() or 0
    avg_income = db.query(func.avg(Lead.annual_income_amount)).scalar() or 0
    emails_sent = db.query(func.count(Lead.id)).filter(Lead.email_sent.is_(True)).scalar() or 0

    by_status = dict(db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all())
    by_tier = dict(db.query(Lead.score_tier, func.count(Lead.id)).group_by(Lead.score_tier).all())
    by_provider = dict(db.query(Lead.provider_type, func.count(Lead.id)).group_by(Lead.provider_type).all())
    by_career_stage = dict(db.query(Lead.career_stage, func.count(Lead.id)).group_by(Lead.career_stage).all())

    converted = by_status.get(LeadStatus.CONVERTED.value, 0)
    app_submitted = by_status.get(LeadStatus.APP_SUBMITTED.value, 0)
    contacted = sum(by_status.get(s, 0) for s in (LeadStatus.CONTACTED.value, LeadStatus.QUALIFIED.value)) + converted + app_submitted
    hot = by_tier.get("hot", 0)

    return DashboardStats(
        total_leads=total,
        by_status=by_status,
        by_tier=by_tier,
        by_provider=by_provider,
        by_career_stage=by_career_stage,
        avg_income=round(float(avg_income), 0),
        conversion_rate=round(((converted + app_submitted) / total) * 100, 1) if total else 0.0,
        contacted_rate=round((contacted / total) * 100, 1) if total else 0.0,
        hot_leads=hot,
        emails_sent=emails_sent,
    )


def create_follow_up(db: Session, lead: Lead, template_key: str, *, custom_message: str | None = None,
                     actor: str = "admin", ip: str | None = None) -> FollowUp:
    full_name = decrypt_field(lead.full_name_enc) or "there"
    rendered = render_template(template_key, first_name=_first_name(full_name), specialty=lead.specialty,
                               career_stage=lead.career_stage, place_of_work=lead.place_of_work, work_state=lead.work_state,
                               custom_message=custom_message)
    follow_up = FollowUp(lead_id=lead.id, template_key=template_key, subject=rendered.subject, body=rendered.body)
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    log_audit(db, action="create_follow_up", entity_type="follow_up", entity_id=follow_up.id, actor=actor,
              details=f"template={template_key} lead={lead.id}", ip_address=ip)
    return follow_up


def leads_to_export_rows(leads: list[Lead], *, include_pii: bool = True) -> list[dict]:
    rows = []
    for lead in leads:
        rows.append({
            "id": lead.id,
            "full_name": decrypt_field(lead.full_name_enc) if include_pii else "REDACTED",
            "email": decrypt_field(lead.email_enc) if include_pii else "REDACTED",
            "phone": decrypt_field(lead.phone_enc) if include_pii else "REDACTED",
            "contact_preference": lead.contact_preference,
            "date_of_birth": decrypt_field(lead.dob_enc) if include_pii else "REDACTED",
            "marital_status": lead.marital_status,
            "dependents_count": lead.dependents_count,
            "address": f"{decrypt_field(lead.address_street_enc) if include_pii else 'REDACTED'}, {lead.address_city}, {lead.address_state} {lead.address_zip}",
            "specialty": lead.specialty,
            "occupation_title": lead.occupation_title,
            "employer": lead.place_of_work,
            "annual_income": lead.annual_income_amount,
            "score": lead.score,
            "score_tier": lead.score_tier,
            "reason_for_applying": decrypt_field(lead.reason_for_applying_enc) if include_pii else "REDACTED",
            "medical_conditions": decrypt_field(lead.medical_conditions_enc) if include_pii else "REDACTED",
            "status": lead.status,
            "email_sent": lead.email_sent,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
        })
    return rows