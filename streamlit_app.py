"""Mutual Income Protection — CRM dashboard with passkey security."""

from __future__ import annotations

import os
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Mutual Income Protection"
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("ADMIN_API_KEY", "dev-only-change-me")
ADMIN_PASSKEY = os.getenv("ADMIN_PASSKEY", "change-me-passkey")

st.set_page_config(page_title=f"{APP_NAME} CRM", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.stApp { background:#F5F7FA; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#001E45,#002F6C); }
[data-testid="stSidebar"] * { color:#fff !important; }
h1,h2,h3 { color:#002F6C !important; }
.brand-header { background:linear-gradient(135deg,#001E45,#002F6C); color:#fff; padding:1rem 1.25rem;
  border-radius:8px; border-bottom:4px solid #C4A962; margin-bottom:1rem; }
</style>
""", unsafe_allow_html=True)


def require_auth() -> bool:
    if st.session_state.get("mip_authenticated"):
        return True
    st.markdown(f'<div class="brand-header"><h2 style="color:#fff!important;margin:0;">{APP_NAME}</h2>'
                '<p style="margin:0.25rem 0 0;opacity:0.9;">Admin CRM — Passkey Required</p></div>', unsafe_allow_html=True)
    st.warning("Enter your admin passkey to access applications, analytics, and exports.")
    pk = st.text_input("Admin Passkey", type="password")
    if st.button("Unlock CRM", type="primary"):
        if pk == ADMIN_PASSKEY:
            st.session_state["mip_authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid passkey.")
    return False


def api_headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def api_get(path: str, **params):
    with httpx.Client(base_url=API_BASE, timeout=30.0) as c:
        r = c.get(path, headers=api_headers(), params=params)
        r.raise_for_status()
        return r.json()


def api_patch(path: str, payload: dict):
    with httpx.Client(base_url=API_BASE, timeout=30.0) as c:
        r = c.patch(path, headers=api_headers(), json=payload)
        r.raise_for_status()
        return r.json()


def api_post(path: str, payload: dict):
    with httpx.Client(base_url=API_BASE, timeout=30.0) as c:
        r = c.post(path, headers=api_headers(), json=payload)
        r.raise_for_status()
        return r.json()


def api_delete(path: str):
    with httpx.Client(base_url=API_BASE, timeout=30.0) as c:
        r = c.delete(path, headers=api_headers())
        r.raise_for_status()


def download_export(fmt: str, pii: bool) -> bytes:
    with httpx.Client(base_url=API_BASE, timeout=60.0) as c:
        r = c.get(f"/api/exports/leads.{fmt}", headers=api_headers(), params={"include_pii": str(pii).lower()})
        r.raise_for_status()
        return r.content


STATUSES = ["new", "contacted", "qualified", "app_submitted", "converted", "declined", "lost", "unsubscribed"]


def render_crm(d: dict) -> None:
    st.subheader(f"Application #{d['id']} — {d['full_name']}")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Score", f"{d['score']} ({d['score_tier']})")
    m2.metric("Income", f"${d['annual_income_amount']:,}")
    m3.metric("BMI", d.get("bmi") or "—")
    m4.metric("Email Sent", "Yes" if d.get("email_sent") else "No")
    m5.metric("Status", d["status"])
    if d.get("score_breakdown"):
        with st.expander("AI Score Breakdown", expanded=True):
            st.dataframe(pd.DataFrame([{"factor": k, "pts": v} for k, v in d["score_breakdown"].items()]),
                         hide_index=True, use_container_width=True)
    tabs = st.tabs(["Personal", "Occupation", "Financial", "Insurance", "Medical", "Disability", "Admin"])
    with tabs[0]:
        st.write(f"**Contact preference:** {d['contact_preference']}")
        st.write(f"**DOB:** {d['date_of_birth']} · **Marital:** {d['marital_status']} · **Dependents:** {d['dependents_count']}")
        st.write(f"**Address:** {d['address_street']}, {d['address_city']}, {d['address_state']} {d['address_zip']}")
        st.text(d.get("dependents_details") or "")
    with tabs[1]:
        st.write(f"**{d['occupation_title']}** — {d['specialty']} ({d['career_stage']})")
        st.write(f"**Employer:** {d['place_of_work']} · {d['hours_worked_per_week']} hrs/wk")
        for k in ("duties_performed", "key_responsibilities", "income_sources", "specialized_skills"):
            if d.get(k): st.markdown(f"**{k.replace('_',' ').title()}:**"); st.text(d[k])
    with tabs[2]:
        st.write(f"**Annual income:** ${d['annual_income_amount']:,}")
        for k in ("income_breakdown", "debts_loans", "major_assets", "monthly_expenses_detail"):
            if d.get(k): st.text(d[k])
    with tabs[3]:
        for k in ("insurance_history", "existing_policies", "prior_applications_denials", "beneficiary_info"):
            if d.get(k): st.text(d[k])
    with tabs[4]:
        st.text(d.get("medical_conditions") or "")
        for k in ("medications", "surgeries", "family_medical_history", "dangerous_activities"):
            if d.get(k): st.text(d[k])
    with tabs[5]:
        st.write(f"**Reason:** {d.get('reason_for_applying','')}")
        for k in ("current_symptoms", "work_impact", "current_disability_details"):
            if d.get(k): st.text(d[k])
    with tabs[6]:
        ns = st.selectbox("Status", STATUSES, index=STATUSES.index(d["status"]))
        notes = st.text_area("Notes", d.get("notes") or "")
        if st.button("Save", type="primary"):
            api_patch(f"/api/leads/{d['id']}", {"status": ns, "notes": notes or None})
            st.success("Saved."); st.rerun()


if not require_auth():
    st.stop()

with st.sidebar:
    st.title(APP_NAME)
    st.caption("Application Simulator CRM")
    page = st.radio("Nav", ["Analytics", "Pipeline", "Application", "Export", "Scoring"], label_visibility="collapsed")
    if st.button("Lock CRM"):
        st.session_state.pop("mip_authenticated", None)
        st.rerun()
    st.divider()
    st.markdown("[Landing](/) · [Apply](/apply)")

st.markdown(f'<div class="brand-header"><h1 style="color:#fff!important;margin:0;font-size:1.4rem;">{APP_NAME}</h1></div>', unsafe_allow_html=True)

try:
    if page == "Analytics":
        s = api_get("/api/dashboard/stats")
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Applications", s["total_leads"])
        c2.metric("Hot Leads", s["hot_leads"])
        c3.metric("Avg Income", f"${s['avg_income']:,.0f}")
        c4.metric("Emails Sent", s.get("emails_sent", 0))
        c5.metric("Conversion", f"{s['conversion_rate']}%")
        c6.metric("Contacted", f"{s['contacted_rate']}%")
        a,b,c = st.columns(3)
        for col, key, title in [(a,"by_career_stage","Career Stage"),(b,"by_tier","Score Tier"),(c,"by_status","Status")]:
            with col:
                if s.get(key):
                    df = pd.DataFrame([{"k":k,"v":v} for k,v in s[key].items()])
                    st.subheader(title); st.bar_chart(df.set_index("k"))

    elif page == "Pipeline":
        leads = api_get("/api/leads")
        if leads:
            df = pd.DataFrame(leads)
            df["income"] = df["annual_income_amount"].apply(lambda x: f"${x:,}")
            st.dataframe(df[["id","full_name","contact_preference","specialty","career_stage","income","score_tier","email_sent","status","created_at"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("No applications yet.")

    elif page == "Application":
        lid = st.number_input("Application ID", min_value=1, step=1)
        if st.button("Load", type="primary"):
            render_crm(api_get(f"/api/leads/{int(lid)}"))

    elif page == "Export":
        st.warning("PII/PHI exports require secure handling.")
        pii = st.checkbox("Include full PII/PHI", True)
        ts = datetime.now().strftime("%Y%m%d")
        st.download_button("CSV", download_export("csv", pii), f"mip_{ts}.csv")
        st.download_button("Excel", download_export("xlsx", pii), f"mip_{ts}.xlsx")

    elif page == "Scoring":
        for item in api_get("/api/dashboard/scoring-criteria"):
            with st.expander(item["label"]):
                st.dataframe(pd.DataFrame([{"opt":k,"pts":v} for k,v in item["weights"].items()]), hide_index=True)

except httpx.ConnectError:
    st.error("API offline — run start.bat")
except httpx.HTTPStatusError as e:
    st.error(f"API {e.response.status_code}: {e.response.text}")