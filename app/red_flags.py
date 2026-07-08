"""Underwriting red-flag detection for Mutual Income Protection leads."""

from __future__ import annotations

from typing import Any


def _yes(value: Any) -> bool:
    return str(value or "").lower() in {"yes", "true", "1"}


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"none", "none reported", "n/a", "—", "-"}


def _bmi_obese(height_feet: int, height_inches: int, weight_lbs: int) -> bool:
    total_inches = height_feet * 12 + height_inches
    if total_inches <= 0:
        return False
    bmi = (weight_lbs / (total_inches**2)) * 703
    return bmi >= 30


def detect_red_flags(data: dict[str, Any]) -> list[dict[str, str]]:
    """Return structured red flags: [{field, label, value, severity}]."""
    flags: list[dict[str, str]] = []

    def add(field: str, label: str, value: str, *, severity: str = "high") -> None:
        flags.append({"field": field, "label": label, "value": value, "severity": severity})

    prescreen_map = {
        "prescreen_disability_leave": "Currently on disability leave or receiving benefits",
        "prescreen_pending_surgery": "Pending surgery or medical procedure",
        "prescreen_hospitalized_12mo": "Hospitalized in the last 12 months",
        "prescreen_uncontrolled_condition": "Uncontrolled chronic medical condition",
        "prescreen_weight_loss_12mo": "Weight loss in the last 12 months",
        "prescreen_bankruptcy_5yr": "Bankruptcy in the last 5 years",
        "prescreen_felony_conviction": "Felony criminal conviction",
        "prescreen_substance_treatment_5yr": "Substance abuse treatment in the last 5 years",
        "prescreen_foreign_travel": "Foreign travel or residence planned",
        "prescreen_aviation_pilot": "Aviation activity (pilot/student pilot/crew)",
        "prescreen_high_risk_avocation": "High-risk avocation (diving, skydiving, racing, etc.)",
        "prescreen_leave_of_absence": "Leave of absence from work",
        "prescreen_family_cardiovascular": "Family cardiovascular disease before age 60",
        "prescreen_family_diabetes_kidney": "Family diabetes, kidney, or familial disorder",
    }
    for field, label in prescreen_map.items():
        if _yes(data.get(field)):
            detail = data.get("prescreen_details") or "Yes"
            add(field, label, str(detail))

    if data.get("current_disability_status") not in (None, "", "none"):
        add(
            "current_disability_status",
            "Non-none disability status",
            str(data.get("current_disability_status")),
        )

    if _yes(data.get("prior_application_denied")):
        add(
            "prior_application_denied",
            "Prior application declined/postponed/rated",
            str(data.get("prior_applications_denials") or "Yes"),
        )

    if data.get("tobacco_nicotine") == "current":
        add("tobacco_nicotine", "Current nicotine/tobacco use", "current")

    if data.get("cannabis_use") == "regular":
        add("cannabis_use", "Regular cannabis use", "regular")

    if data.get("alcohol_use") == "heavy":
        add("alcohol_use", "Heavy alcohol use", "heavy")

    if data.get("drug_use") == "current":
        add("drug_use", "Current drug use", "current")

    if data.get("dui_history") == "yes_within_5_years":
        add("dui_history", "DUI/DWI within 5 years", "yes_within_5_years")

    if data.get("military_status") == "active_duty":
        add("military_status", "Active duty military", "active_duty")

    conditions = data.get("medical_conditions") or []
    if isinstance(conditions, str):
        conditions = [c.strip() for c in conditions.split(";") if c.strip()]
    serious = [c for c in conditions if c and c.lower() != "none reported"]
    if serious:
        add("medical_conditions", "Reported medical conditions", "; ".join(serious), severity="medium")

    if _non_empty(data.get("medical_conditions_other")):
        add("medical_conditions_other", "Other medical conditions", str(data["medical_conditions_other"]), severity="medium")

    if _non_empty(data.get("dangerous_activities")):
        add("dangerous_activities", "Dangerous activities disclosed", str(data["dangerous_activities"]))

    hf = int(data.get("height_feet") or 0)
    hi = int(data.get("height_inches") or 0)
    wl = int(data.get("weight_lbs") or 0)
    if hf and wl and _bmi_obese(hf, hi, wl):
        add("bmi", "BMI in obese range", f"{hf}'{hi}\" / {wl} lbs", severity="medium")

    if _non_empty(data.get("current_symptoms")):
        add("current_symptoms", "Current symptoms reported", str(data["current_symptoms"]), severity="medium")

    if _non_empty(data.get("work_impact")):
        add("work_impact", "Work impact from health issues", str(data["work_impact"]), severity="medium")

    meds = data.get("medications_table") or []
    if isinstance(meds, list) and meds:
        active = [m for m in meds if isinstance(m, dict) and _non_empty(m.get("diagnosis"))]
        if active:
            add("medications_table", "Structured medication/condition entries", f"{len(active)} row(s)", severity="medium")

    return flags