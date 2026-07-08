"""Mutual Income Protection reference data."""

from app.config import APP_NAME

AGENT_CREDENTIAL_LINE = (
    "Licensed American agents with 3+ years of experience — guaranteed."
)

PHYSICIAN_SPECIALTIES = [
    "Anesthesiology", "Cardiology", "Dermatology", "Emergency Medicine", "Family Medicine",
    "Gastroenterology", "Internal Medicine", "Neurology", "Neurosurgery", "Obstetrics & Gynecology",
    "Oncology", "Ophthalmology", "Orthopedic Surgery", "Otolaryngology (ENT)", "Pathology",
    "Pediatrics", "Physical Medicine & Rehabilitation", "Psychiatry", "Pulmonology", "Radiology",
    "General Surgery", "Urology", "Other",
]

DENTAL_SPECIALTIES = [
    "General Dentistry", "Orthodontics", "Oral & Maxillofacial Surgery", "Periodontics",
    "Endodontics", "Prosthodontics", "Pediatric Dentistry", "Other",
]

MEDICAL_CONDITIONS = [
    "None reported", "Anxiety / Depression", "Asthma", "Back / Neck pain", "Cancer (history)",
    "Diabetes", "Heart disease", "High blood pressure", "Migraines", "Sleep apnea",
    "Thyroid disorder", "ADHD", "Autoimmune disorder", "Other",
]

DISCLAIMER = (
    f"{APP_NAME} is an independent disability insurance pre-application tool. "
    "This is an information-gathering tool only — not an insurance application or offer of coverage. "
    f"{AGENT_CREDENTIAL_LINE} An agent will contact you by phone or email after submission, "
    "based on your stated preference."
)

PREMIUM_ACK_TEXT = (
    "✅ I understand that our goal with Mutual Income Protection is to structure coverage while "
    "targeting the cost of insurance to be less than 1-3% of my annual income where possible."
)

AGENT_FOLLOWUP_ACK_TEXT = (
    "I understand this form collects information only. "
    f"{AGENT_CREDENTIAL_LINE} An agent will contact me by my preferred method to discuss options "
    "and collect any additional details needed for a formal carrier application."
)

MEDICAL_EXAM_ACK_TEXT = (
    "I understand that I may be required to complete a medical examination including blood and "
    "urine tests as part of a formal disability insurance application process, if I choose to proceed."
)