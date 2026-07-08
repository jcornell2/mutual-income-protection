from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

class ProviderType(str, Enum):
    PHYSICIAN = "physician"
    DENTIST = "dentist"


class CareerStage(str, Enum):
    RESIDENT = "resident"
    FELLOW = "fellow"
    NEW_ATTENDING = "new_attending"
    ESTABLISHED_ATTENDING = "established_attending"


class LeadCreate(BaseModel):
    # --- Personal ---
    full_name: str = Field(..., min_length=2, max_length=200)
    date_of_birth: date
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=30)
    contact_preference: Literal["phone", "email", "either"] = "either"
    address_street: str = Field(..., min_length=3, max_length=256)
    address_line2: str | None = Field(default=None, max_length=256)
    address_city: str = Field(..., min_length=2, max_length=128)
    address_state: str = Field(..., min_length=2, max_length=32)
    address_zip: str = Field(..., min_length=5, max_length=16)
    gender: Literal["male", "female", "non_binary", "prefer_not_to_say"] | None = None
    marital_status: Literal["single", "married", "domestic_partner", "divorced", "widowed"] = "single"
    dependents_count: int = Field(default=0, ge=0, le=20)
    dependents_details: str | None = Field(default=None, max_length=2000)

    # --- Occupation & duties ---
    provider_type: ProviderType
    career_stage: CareerStage
    specialty: str = Field(..., min_length=2, max_length=128)
    occupation_title: str = Field(..., min_length=2, max_length=128)
    place_of_work: str = Field(..., min_length=2, max_length=256)
    employer_type: Literal["hospital", "private_practice", "academic", "group_practice", "other"] = "hospital"
    duties_performed: str = Field(..., min_length=10, max_length=3000)
    hours_worked_per_week: int = Field(..., ge=1, le=120)
    income_sources: str = Field(..., min_length=5, max_length=2000)
    key_responsibilities: str = Field(..., min_length=5, max_length=2000)
    specialized_skills: str | None = Field(default=None, max_length=2000)
    occupation_details: str | None = Field(default=None, max_length=2000)
    training_program: str | None = Field(default=None, max_length=256)
    work_city: str = Field(..., min_length=2, max_length=128)
    work_state: str = Field(..., min_length=2, max_length=32)
    work_zip: str | None = Field(default=None, max_length=16)
    license_state: str | None = Field(default=None, max_length=32)
    graduation_year: int | None = Field(default=None, ge=1970, le=2040)
    years_in_practice: int | None = Field(default=None, ge=0, le=60)

    # --- Financial ---
    annual_income_amount: int = Field(..., ge=0, le=10_000_000)
    income_breakdown: str = Field(..., min_length=5, max_length=2000)
    monthly_expenses_range: Literal["under_3k", "3k_8k", "8k_15k", "15k_plus", "not_sure"]
    monthly_expenses_detail: str | None = Field(default=None, max_length=2000)
    home_value_range: Literal["none", "under_300k", "300k_600k", "600k_1m", "1m_plus", "unknown"] = "unknown"
    vehicles_value_range: Literal["none", "under_25k", "25k_75k", "75k_plus", "unknown"] = "unknown"
    major_assets: str | None = Field(default=None, max_length=2000)
    debts_loans: str = Field(..., min_length=3, max_length=2000)
    student_loans_range: Literal["none", "under_100k", "100_300k", "300k_plus", "unknown"] = "unknown"
    assets_range: Literal["under_100k", "100k_500k", "500k_1m", "1m_plus", "unknown"] = "unknown"
    desired_monthly_benefit: Literal["under_5k", "5k_10k", "10k_15k", "15k_plus", "not_sure"] | None = None

    # --- Insurance history ---
    existing_disability_insurance: Literal["yes", "no", "unsure"] = "no"
    existing_life_insurance: Literal["yes", "no", "unsure"] = "no"
    health_insurance_status: Literal["employer", "marketplace", "spouse", "none", "other"] = "employer"
    existing_policies: str | None = Field(default=None, max_length=3000)
    insurance_history: str | None = Field(default=None, max_length=3000)
    prior_application_denied: Literal["yes", "no", "unsure"] = "no"
    prior_applications_denials: str | None = Field(default=None, max_length=2000)
    group_coverage_through_employer: Literal["yes", "no", "unsure"] = "unsure"
    beneficiary_info: str | None = Field(default=None, max_length=1000)

    # --- Medical & health ---
    height_feet: int = Field(..., ge=4, le=7)
    height_inches: int = Field(..., ge=0, le=11)
    weight_lbs: int = Field(..., ge=80, le=500)
    tobacco_nicotine: Literal["never", "former", "current"]
    cannabis_use: Literal["never", "occasional", "regular"]
    alcohol_use: Literal["none", "social", "moderate", "heavy"]
    drug_use: Literal["never", "former", "current"] = "never"
    medical_conditions: list[str] = Field(default_factory=list)
    medical_conditions_other: str | None = Field(default=None, max_length=3000)
    medications: str | None = Field(default=None, max_length=3000)
    surgeries: str | None = Field(default=None, max_length=3000)
    family_medical_history: str | None = Field(default=None, max_length=3000)
    exercise_frequency: Literal["none", "light", "moderate", "intense"] = "moderate"
    hobbies_activities: str | None = Field(default=None, max_length=2000)
    travel_frequency: Literal["rare", "occasional", "frequent", "international"] = "occasional"
    dangerous_activities: str | None = Field(default=None, max_length=2000)
    dui_history: Literal["none", "yes_over_5_years", "yes_within_5_years"]
    military_status: Literal["none", "active_duty", "reserve", "veteran"]

    # --- Disability specific ---
    current_disability_status: Literal["none", "currently_disabled", "prior_claim", "receiving_benefits"]
    current_disability_details: str | None = Field(default=None, max_length=2000)
    reason_for_applying: str = Field(..., min_length=10, max_length=2000)
    current_symptoms: str | None = Field(default=None, max_length=2000)
    work_impact: str | None = Field(default=None, max_length=2000)

    referral_source: Literal[
        "web", "colleague", "financial_advisor", "program_director", "conference", "social_media", "other"
    ] = "web"
    notes: str | None = Field(default=None, max_length=2000)

    # --- Consents & disclosures ---
    privacy_consent: bool = False
    medical_exam_acknowledgment: bool = False
    agent_followup_acknowledgment: bool = False
    premium_target_acknowledgment: bool = False

    @field_validator("privacy_consent", "medical_exam_acknowledgment", "agent_followup_acknowledgment", "premium_target_acknowledgment")
    @classmethod
    def require_ack(cls, value: bool) -> bool:
        if not value:
            raise ValueError("All required acknowledgments must be accepted.")
        return value

    @model_validator(mode="after")
    def validate_conditional(self):
        if self.career_stage in (CareerStage.RESIDENT, CareerStage.FELLOW) and not self.training_program:
            raise ValueError("Training program is required for residents and fellows.")
        if self.current_disability_status != "none" and not self.current_disability_details:
            raise ValueError("Please describe your disability status.")
        if self.prior_application_denied == "yes" and not self.prior_applications_denials:
            raise ValueError("Please describe prior application denials.")
        return self


class LeadUpdate(BaseModel):
    status: Literal[
        "new", "contacted", "qualified", "app_submitted", "converted", "declined", "lost", "unsubscribed"
    ] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class LeadResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    date_of_birth: str
    contact_preference: str
    address_street: str
    address_line2: str | None
    address_city: str
    address_state: str
    address_zip: str
    marital_status: str
    dependents_count: int
    dependents_details: str | None
    gender: str | None
    provider_type: str
    career_stage: str
    specialty: str
    occupation_title: str
    place_of_work: str
    employer_type: str
    duties_performed: str | None
    hours_worked_per_week: int
    income_sources: str | None
    key_responsibilities: str | None
    specialized_skills: str | None
    occupation_details: str | None
    training_program: str | None
    work_city: str
    work_state: str
    work_zip: str | None
    license_state: str | None
    graduation_year: int | None
    years_in_practice: int | None
    annual_income_amount: int
    annual_income_range: str
    income_breakdown: str | None
    monthly_expenses_range: str
    monthly_expenses_detail: str | None
    home_value_range: str
    vehicles_value_range: str
    major_assets: str | None
    debts_loans: str | None
    height_feet: int
    height_inches: int
    weight_lbs: int
    bmi: float | None
    medical_conditions: str | None
    medications: str | None
    surgeries: str | None
    family_medical_history: str | None
    exercise_frequency: str
    hobbies_activities: str | None
    travel_frequency: str
    dangerous_activities: str | None
    tobacco_nicotine: str
    cannabis_use: str
    alcohol_use: str
    drug_use: str
    dui_history: str
    military_status: str
    current_disability_status: str
    current_disability_details: str | None
    health_insurance_status: str
    prior_application_denied: str
    prior_applications_denials: str | None
    insurance_history: str | None
    existing_disability_insurance: str
    existing_life_insurance: str
    existing_policies: str | None
    group_coverage_through_employer: str
    beneficiary_info: str | None
    assets_range: str
    student_loans_range: str
    desired_monthly_benefit: str | None
    reason_for_applying: str | None
    current_symptoms: str | None
    work_impact: str | None
    referral_source: str
    status: str
    score: int
    score_tier: str
    score_breakdown: dict[str, int] | None
    email_sent: bool
    privacy_consent: bool
    medical_exam_acknowledgment: bool
    agent_followup_acknowledgment: bool
    premium_target_acknowledgment: bool
    consent_timestamp: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    contacted_at: datetime | None
    converted_at: datetime | None

    model_config = {"from_attributes": True}


class LeadSummary(BaseModel):
    id: int
    full_name: str
    email: str
    contact_preference: str
    provider_type: str
    career_stage: str
    specialty: str
    occupation_title: str
    place_of_work: str
    address_state: str
    annual_income_amount: int
    current_disability_status: str
    status: str
    score: int
    score_tier: str
    email_sent: bool
    created_at: datetime


class DashboardStats(BaseModel):
    total_leads: int
    by_status: dict[str, int]
    by_tier: dict[str, int]
    by_provider: dict[str, int]
    by_career_stage: dict[str, int]
    avg_income: float
    conversion_rate: float
    contacted_rate: float
    hot_leads: int
    emails_sent: int


class FollowUpCreate(BaseModel):
    template_key: str
    custom_message: str | None = None


class FollowUpResponse(BaseModel):
    id: int
    lead_id: int
    template_key: str
    subject: str
    body: str
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailTemplatePreview(BaseModel):
    key: str
    name: str
    subject: str
    body: str