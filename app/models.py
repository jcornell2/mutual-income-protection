from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

SCHEMA_VERSION = 5


class Base(DeclarativeBase):
    pass


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    APP_SUBMITTED = "app_submitted"
    CONVERTED = "converted"
    DECLINED = "declined"
    LOST = "lost"
    UNSUBSCRIBED = "unsubscribed"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Encrypted PII / PHI / financial
    full_name_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    email_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    phone_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    dob_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    ssn_enc: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address_street_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    address_line2_enc: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dependents_details_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    duties_performed_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    income_sources_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_responsibilities_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialized_skills_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    income_breakdown_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_expenses_detail_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    major_assets_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    debts_loans_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    insurance_history_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    prior_applications_denials_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_conditions_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    medications_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    surgeries_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_medical_history_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    hobbies_activities_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    dangerous_activities_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_disability_details_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    existing_policies_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    beneficiary_info_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason_for_applying_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_symptoms_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_impact_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation_details_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    email_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ssn_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    contact_preference: Mapped[str] = mapped_column(String(16), default="either")

    address_city: Mapped[str] = mapped_column(String(128), nullable=False)
    address_state: Mapped[str] = mapped_column(String(32), nullable=False)
    address_zip: Mapped[str] = mapped_column(String(16), nullable=False)
    marital_status: Mapped[str] = mapped_column(String(32), default="single")
    dependents_count: Mapped[int] = mapped_column(Integer, default=0)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)

    provider_type: Mapped[str] = mapped_column(String(16), nullable=False)
    career_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    specialty: Mapped[str] = mapped_column(String(128), nullable=False)
    occupation_title: Mapped[str] = mapped_column(String(128), nullable=False)
    place_of_work: Mapped[str] = mapped_column(String(256), nullable=False)
    employer_type: Mapped[str] = mapped_column(String(32), default="hospital")
    hours_worked_per_week: Mapped[int] = mapped_column(Integer, default=40)
    training_program: Mapped[str | None] = mapped_column(String(256), nullable=True)
    work_city: Mapped[str] = mapped_column(String(128), nullable=False)
    work_state: Mapped[str] = mapped_column(String(32), nullable=False)
    work_zip: Mapped[str | None] = mapped_column(String(16), nullable=True)
    license_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    years_in_practice: Mapped[int | None] = mapped_column(Integer, nullable=True)

    height_feet: Mapped[int] = mapped_column(Integer, nullable=False)
    height_inches: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_lbs: Mapped[int] = mapped_column(Integer, nullable=False)

    tobacco_nicotine: Mapped[str] = mapped_column(String(16), nullable=False)
    cannabis_use: Mapped[str] = mapped_column(String(16), nullable=False)
    alcohol_use: Mapped[str] = mapped_column(String(16), nullable=False)
    drug_use: Mapped[str] = mapped_column(String(16), default="never")
    dui_history: Mapped[str] = mapped_column(String(16), nullable=False)
    military_status: Mapped[str] = mapped_column(String(16), nullable=False)
    exercise_frequency: Mapped[str] = mapped_column(String(32), default="moderate")
    travel_frequency: Mapped[str] = mapped_column(String(32), default="occasional")

    current_disability_status: Mapped[str] = mapped_column(String(32), nullable=False)
    health_insurance_status: Mapped[str] = mapped_column(String(32), default="employer")
    prior_application_denied: Mapped[str] = mapped_column(String(16), default="no")

    annual_income_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_income_range: Mapped[str] = mapped_column(String(32), nullable=False)
    monthly_expenses_range: Mapped[str] = mapped_column(String(32), nullable=False)
    home_value_range: Mapped[str] = mapped_column(String(32), default="unknown")
    vehicles_value_range: Mapped[str] = mapped_column(String(32), default="unknown")
    student_loans_range: Mapped[str] = mapped_column(String(32), default="unknown")
    desired_monthly_benefit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    existing_disability_insurance: Mapped[str] = mapped_column(String(16), default="no")
    existing_life_insurance: Mapped[str] = mapped_column(String(16), default="no")
    group_coverage_through_employer: Mapped[str] = mapped_column(String(16), default="unknown")
    assets_range: Mapped[str] = mapped_column(String(32), default="unknown")

    referral_source: Mapped[str] = mapped_column(String(32), default="web")

    status: Mapped[str] = mapped_column(String(32), default=LeadStatus.NEW.value, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    score_tier: Mapped[str] = mapped_column(String(16), default="cold")
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    privacy_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_exam_acknowledgment: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_followup_acknowledgment: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_target_acknowledgment: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    follow_ups: Mapped[list["FollowUp"]] = relationship(back_populates="lead", cascade="all, delete-orphan")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    template_key: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lead: Mapped["Lead"] = relationship(back_populates="follow_ups")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor: Mapped[str] = mapped_column(String(128), default="system")
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SchemaMeta(Base):
    __tablename__ = "schema_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)