"""Build complete HTML/text alert emails for new lead submissions."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from app.config import APP_NAME
from app.constants import ADVISOR_LINE, AGENT_CREDENTIAL_LINE
from app.red_flags import detect_red_flags

FIELD_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Pre-Screen Red Flags",
        [
            ("prescreen_disability_leave", "On disability leave / receiving benefits?"),
            ("prescreen_pending_surgery", "Pending surgery or procedure?"),
            ("prescreen_hospitalized_12mo", "Hospitalized in last 12 months?"),
            ("prescreen_uncontrolled_condition", "Uncontrolled chronic condition?"),
            ("prescreen_weight_loss_12mo", "Weight loss in last 12 months?"),
            ("prescreen_weight_loss_lbs", "Weight loss amount (lbs)"),
            ("prescreen_bankruptcy_5yr", "Bankruptcy in last 5 years?"),
            ("prescreen_felony_conviction", "Felony conviction?"),
            ("prescreen_substance_treatment_5yr", "Substance treatment in last 5 years?"),
            ("prescreen_foreign_travel", "Foreign travel/residence planned?"),
            ("prescreen_aviation_pilot", "Aviation (pilot/student pilot/crew)?"),
            ("prescreen_high_risk_avocation", "High-risk avocations?"),
            ("prescreen_leave_of_absence", "Leave of absence from work?"),
            ("prescreen_family_cardiovascular", "Family CV disease before age 60?"),
            ("prescreen_family_diabetes_kidney", "Family diabetes/kidney/familial disorder?"),
            ("prescreen_details", "Pre-screen details / explanations"),
        ],
    ),
    (
        "Personal Information",
        [
            ("full_name", "Full name"),
            ("date_of_birth", "Date of birth"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("contact_preference", "Contact preference"),
            ("address_street", "Street"),
            ("address_line2", "Address line 2"),
            ("address_city", "City"),
            ("address_state", "State"),
            ("address_zip", "ZIP"),
            ("gender", "Gender"),
            ("marital_status", "Marital status"),
            ("dependents_count", "Dependents count"),
            ("dependents_details", "Dependents details"),
        ],
    ),
    (
        "Occupation & Duties (Survey A3050 §9)",
        [
            ("provider_type", "Provider type"),
            ("career_stage", "Career stage"),
            ("specialty", "Specialty"),
            ("occupation_title", "Occupation title"),
            ("place_of_work", "Place of work"),
            ("employer_type", "Employer type"),
            ("hours_worked_per_week", "Hours/week"),
            ("work_city", "Work city"),
            ("work_state", "Work state"),
            ("work_zip", "Work ZIP"),
            ("training_program", "Training program"),
            ("license_state", "License state"),
            ("graduation_year", "Graduation year"),
            ("years_in_practice", "Years in practice"),
            ("duties_performed", "Duties performed"),
            ("income_sources", "Income sources"),
            ("key_responsibilities", "Key responsibilities"),
            ("specialized_skills", "Specialized skills"),
            ("occupation_details", "Additional occupation details"),
        ],
    ),
    (
        "Financial Profile",
        [
            ("annual_income_amount", "Annual income ($)"),
            ("annual_unearned_income", "Annual unearned income ($)"),
            ("income_breakdown", "Income breakdown"),
            ("monthly_expenses_range", "Monthly expenses range"),
            ("monthly_expenses_detail", "Monthly expenses detail"),
            ("desired_monthly_benefit", "Desired monthly benefit"),
            ("home_value_range", "Home value"),
            ("vehicles_value_range", "Vehicles value"),
            ("student_loans_range", "Student loans"),
            ("assets_range", "Total assets"),
            ("major_assets", "Major assets"),
            ("debts_loans", "Debts & loans"),
        ],
    ),
    (
        "Insurance History",
        [
            ("existing_disability_insurance", "Existing disability insurance"),
            ("existing_life_insurance", "Existing life insurance"),
            ("health_insurance_status", "Health insurance status"),
            ("group_coverage_through_employer", "Group DI through employer"),
            ("prior_application_denied", "Prior application denied"),
            ("prior_applications_denials", "Prior denials detail"),
            ("existing_policies", "Existing policies"),
            ("insurance_history", "Insurance history"),
            ("beneficiary_info", "Beneficiary info"),
        ],
    ),
    (
        "Medical & Health (Survey A3050 §14–16)",
        [
            ("height_feet", "Height (ft)"),
            ("height_inches", "Height (in)"),
            ("weight_lbs", "Weight (lbs)"),
            ("bmi", "BMI"),
            ("tobacco_nicotine", "Nicotine/tobacco"),
            ("cannabis_use", "Cannabis use"),
            ("alcohol_use", "Alcohol use"),
            ("drug_use", "Drug use"),
            ("medical_conditions", "Medical conditions"),
            ("medical_conditions_other", "Other conditions"),
            ("medications", "Medications (free text)"),
            ("surgeries", "Surgeries / hospitalizations"),
            ("family_medical_history", "Family medical history"),
        ],
    ),
    (
        "Lifestyle & Risk (Survey A3050 §21–22)",
        [
            ("exercise_frequency", "Exercise frequency"),
            ("travel_frequency", "Travel frequency"),
            ("dui_history", "DUI/DWI history"),
            ("military_status", "Military status"),
            ("hobbies_activities", "Hobbies & activities"),
            ("dangerous_activities", "Dangerous activities"),
        ],
    ),
    (
        "Disability Details",
        [
            ("current_disability_status", "Disability status"),
            ("current_disability_details", "Disability details"),
            ("reason_for_applying", "Reason for applying"),
            ("current_symptoms", "Current symptoms"),
            ("work_impact", "Work impact"),
            ("referral_source", "Referral source"),
            ("notes", "Additional notes"),
        ],
    ),
    (
        "Consent & Authorization Proof",
        [
            ("privacy_consent", "Privacy consent"),
            ("medical_exam_acknowledgment", "Physical exam (blood/urine) acknowledgment"),
            ("agent_followup_acknowledgment", "Agent follow-up acknowledgment"),
            ("premium_target_acknowledgment", "1–3% income premium target acknowledgment"),
            ("formal_app_acknowledgment", "SSN/payment formal application acknowledgment"),
            ("consent_timestamp", "Consent timestamp (UTC)"),
        ],
    ),
]


def _fmt_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "✅ YES" if value else "No"
    if isinstance(value, (list, tuple)):
        if not value:
            return "—"
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, indent=2)
    if isinstance(value, int) and value >= 1000:
        return f"{value:,}"
    return str(value)


def _esc(text: str) -> str:
    return html.escape(text, quote=True).replace("\n", "<br>")


def _medication_table_html(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p><em>No structured medication rows submitted.</em></p>"
    headers = [
        "Diagnosis",
        "Medication / Treatment",
        "Still Under Treatment",
        "Onset Date",
        "Physician",
        "Facility / Address",
    ]
    keys = [
        "diagnosis",
        "medication_treatment",
        "still_under_treatment",
        "onset_date",
        "physician_name",
        "facility_address",
    ]
    th = "".join(f"<th style='padding:8px;border:1px solid #D4DCE6;background:#F5F7FA;'>{h}</th>" for h in headers)
    body_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not any(str(row.get(k) or "").strip() for k in keys):
            continue
        tds = "".join(
            f"<td style='padding:8px;border:1px solid #D4DCE6;vertical-align:top;'>{_esc(_fmt_value(row.get(k)))}</td>"
            for k in keys
        )
        body_rows.append(f"<tr>{tds}</tr>")
    if not body_rows:
        return "<p><em>No structured medication rows submitted.</em></p>"
    return (
        "<table style='width:100%;border-collapse:collapse;font-size:13px;margin-top:8px;'>"
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
    )


def _section_html(title: str, fields: list[tuple[str, str]], data: dict[str, Any], red_flag_fields: set[str]) -> str:
    rows = []
    for key, label in fields:
        value = data.get(key)
        if value is None or value == "" or value == []:
            continue
        highlight = "background:#fdecec;border-left:4px solid #b42318;" if key in red_flag_fields else ""
        rows.append(
            f"<tr style='{highlight}'>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #E8EDF2;font-weight:600;width:38%;vertical-align:top;'>{_esc(label)}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #E8EDF2;vertical-align:top;'>{_esc(_fmt_value(value))}</td>"
            "</tr>"
        )
    if not rows:
        return ""
    return (
        f"<h3 style='color:#002F6C;margin:24px 0 8px;font-size:16px;'>{_esc(title)}</h3>"
        f"<table style='width:100%;border-collapse:collapse;font-size:14px;'>{''.join(rows)}</table>"
    )


def build_lead_alert_email(
    *,
    lead_id: int,
    data: dict[str, Any],
    submitted_at: datetime | None = None,
) -> tuple[str, str, str]:
    """Return (subject, html_body, text_body)."""
    name = data.get("full_name") or "Applicant"
    score = data.get("score", "—")
    tier = data.get("score_tier", "—")
    ts = submitted_at or data.get("consent_timestamp") or data.get("created_at")
    ts_str = ts.isoformat() if hasattr(ts, "isoformat") else (str(ts) if ts else "—")

    red_flags = detect_red_flags(data)
    red_flag_fields = {f["field"] for f in red_flags}

    subject = f"[{APP_NAME}] 🔔 Lead #{lead_id} — {name} — Score {score} ({tier})"
    if red_flags:
        subject += f" — {len(red_flags)} RED FLAG(S)"

    breakdown = data.get("score_breakdown") or {}
    breakdown_html = ""
    breakdown_text = ""
    if breakdown:
        breakdown_html = "<ul>" + "".join(
            f"<li><strong>{_esc(k)}:</strong> {v}</li>" for k, v in breakdown.items()
        ) + "</ul>"
        breakdown_text = "\n".join(f"  {k}: {v}" for k, v in breakdown.items())

    flags_html = ""
    flags_text = ""
    if red_flags:
        flag_items_html = "".join(
            f"<li style='margin-bottom:6px;'><strong>{_esc(f['label'])}</strong> — {_esc(f['value'])} "
            f"<span style='color:#b42318;font-size:12px;'>({f['severity']})</span></li>"
            for f in red_flags
        )
        flags_html = (
            "<div style='background:#fdecec;border:2px solid #b42318;border-radius:8px;padding:16px;margin:16px 0;'>"
            f"<h3 style='color:#b42318;margin:0 0 8px;'>⚠️ RED FLAGS ({len(red_flags)})</h3>"
            f"<ul style='margin:0;padding-left:20px;'>{flag_items_html}</ul></div>"
        )
        flags_text = "RED FLAGS:\n" + "\n".join(
            f"  - {f['label']}: {f['value']} ({f['severity']})" for f in red_flags
        )

    sections_html = "".join(
        _section_html(title, fields, data, red_flag_fields) for title, fields in FIELD_SECTIONS
    )

    meds = data.get("medications_table") or []
    meds_section = (
        "<h3 style='color:#002F6C;margin:24px 0 8px;font-size:16px;'>Medication Table (Survey A3050)</h3>"
        + _medication_table_html(meds if isinstance(meds, list) else [])
    )

    html_body = f"""
    <html><body style="font-family:Segoe UI,Arial,sans-serif;color:#1A2B3C;margin:0;padding:0;">
    <div style="max-width:760px;margin:0 auto;border:1px solid #D4DCE6;border-radius:8px;overflow:hidden;">
      <div style="background:#002F6C;color:#fff;padding:20px;border-bottom:4px solid #C4A962;">
        <h2 style="margin:0;">{APP_NAME}</h2>
        <p style="margin:8px 0 0;opacity:0.92;">New pre-application submission — {ADVISOR_LINE}</p>
      </div>
      <div style="padding:20px;">
        <table style="width:100%;font-size:14px;margin-bottom:8px;">
          <tr><td style="padding:4px 0;"><strong>Lead ID:</strong> #{lead_id}</td></tr>
          <tr><td style="padding:4px 0;"><strong>Submitted:</strong> {_esc(ts_str)}</td></tr>
          <tr><td style="padding:4px 0;"><strong>AI Score:</strong> {score}/100 ({_esc(str(tier))} tier)</td></tr>
          <tr><td style="padding:4px 0;"><strong>Email delivery:</strong> Complete application data below</td></tr>
        </table>
        {flags_html}
        <h3 style="color:#002F6C;margin:16px 0 8px;">Score Breakdown</h3>
        {breakdown_html or "<p><em>No breakdown available.</em></p>"}
        {sections_html}
        {meds_section}
        <hr style="border:none;border-top:1px solid #D4DCE6;margin:24px 0;">
        <p style="font-size:12px;color:#5A6B7D;line-height:1.5;">
          {AGENT_CREDENTIAL_LINE} Follow up per applicant contact preference.<br>
          SSN and payment details collected only during formal carrier application.
        </p>
      </div>
    </div>
    </body></html>
    """

    text_sections = []
    for title, fields in FIELD_SECTIONS:
        lines = [f"\n=== {title} ==="]
        for key, label in fields:
            val = data.get(key)
            if val is None or val == "" or val == []:
                continue
            lines.append(f"{label}: {_fmt_value(val)}")
        if len(lines) > 1:
            text_sections.append("\n".join(lines))

    text_body = (
        f"{APP_NAME} — Lead #{lead_id}\n"
        f"Submitted: {ts_str}\n"
        f"Score: {score}/100 ({tier})\n"
        f"{flags_text}\n"
        f"Score breakdown:\n{breakdown_text or '  (none)'}\n"
        + "\n".join(text_sections)
        + "\n\nMedication table:\n"
        + (json.dumps(meds, indent=2) if meds else "  (none)")
    )

    return subject, html_body, text_body