"""Admin CRM views — direct database access (no API required)."""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from app.schemas import LeadUpdate
from app.scoring import get_scoring_criteria_for_display
from app.services import (
    get_dashboard_stats,
    get_lead,
    lead_to_response,
    lead_to_summary,
    leads_to_export_rows,
    list_leads,
    update_lead,
)
from frontend.db import get_session

STATUSES = ["new", "contacted", "qualified", "app_submitted", "converted", "declined", "lost", "unsubscribed"]


def _lead_dict(lead_id: int) -> dict:
    with get_session() as db:
        lead = get_lead(db, lead_id)
        if not lead:
            raise ValueError(f"Application #{lead_id} not found.")
        return lead_to_response(lead).model_dump()


def render_application_detail(d: dict) -> None:
    st.subheader(f"Application #{d['id']} — {d['full_name']}")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Score", f"{d['score']} ({d['score_tier']})")
    m2.metric("Income", f"${d['annual_income_amount']:,}")
    m3.metric("BMI", d.get("bmi") or "—")
    m4.metric("Email Sent", "Yes" if d.get("email_sent") else "No")
    m5.metric("Status", d["status"])
    if d.get("score_breakdown"):
        with st.expander("AI Score Breakdown", expanded=True):
            st.dataframe(
                pd.DataFrame([{"factor": k, "pts": v} for k, v in d["score_breakdown"].items()]),
                hide_index=True,
                use_container_width=True,
            )
    tabs = st.tabs(["Personal", "Occupation", "Financial", "Insurance", "Medical", "Disability", "Admin"])
    with tabs[0]:
        st.write(f"**Contact preference:** {d['contact_preference']}")
        st.write(
            f"**DOB:** {d['date_of_birth']} · **Marital:** {d['marital_status']} · "
            f"**Dependents:** {d['dependents_count']}"
        )
        st.write(f"**Address:** {d['address_street']}, {d['address_city']}, {d['address_state']} {d['address_zip']}")
        st.text(d.get("dependents_details") or "")
    with tabs[1]:
        st.write(f"**{d['occupation_title']}** — {d['specialty']} ({d['career_stage']})")
        st.write(f"**Employer:** {d['place_of_work']} · {d['hours_worked_per_week']} hrs/wk")
        for k in ("duties_performed", "key_responsibilities", "income_sources", "specialized_skills"):
            if d.get(k):
                st.markdown(f"**{k.replace('_', ' ').title()}:**")
                st.text(d[k])
    with tabs[2]:
        st.write(f"**Annual income:** ${d['annual_income_amount']:,}")
        for k in ("income_breakdown", "debts_loans", "major_assets", "monthly_expenses_detail"):
            if d.get(k):
                st.text(d[k])
    with tabs[3]:
        for k in ("insurance_history", "existing_policies", "prior_applications_denials", "beneficiary_info"):
            if d.get(k):
                st.text(d[k])
    with tabs[4]:
        st.text(d.get("medical_conditions") or "")
        for k in ("medications", "surgeries", "family_medical_history", "dangerous_activities"):
            if d.get(k):
                st.text(d[k])
    with tabs[5]:
        st.write(f"**Reason:** {d.get('reason_for_applying', '')}")
        for k in ("current_symptoms", "work_impact", "current_disability_details"):
            if d.get(k):
                st.text(d[k])
    with tabs[6]:
        ns = st.selectbox("Status", STATUSES, index=STATUSES.index(d["status"]))
        notes = st.text_area("Notes", d.get("notes") or "")
        if st.button("Save", type="primary", key=f"save_lead_{d['id']}"):
            with get_session() as db:
                lead = get_lead(db, d["id"])
                if lead:
                    update_lead(db, lead, LeadUpdate(status=ns, notes=notes or None), actor="admin_crm")
            st.success("Saved.")
            st.rerun()


def render_analytics() -> None:
    with get_session() as db:
        s = get_dashboard_stats(db)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Applications", s.total_leads)
    c2.metric("Hot Leads", s.hot_leads)
    c3.metric("Avg Income", f"${s.avg_income:,.0f}")
    c4.metric("Emails Sent", s.emails_sent)
    c5.metric("Conversion", f"{s.conversion_rate}%")
    c6.metric("Contacted", f"{s.contacted_rate}%")
    a, b, c = st.columns(3)
    for col, key, title in [
        (a, s.by_career_stage, "Career Stage"),
        (b, s.by_tier, "Score Tier"),
        (c, s.by_status, "Status"),
    ]:
        with col:
            if key:
                df = pd.DataFrame([{"k": k, "v": v} for k, v in key.items()])
                st.subheader(title)
                st.bar_chart(df.set_index("k"))


def render_pipeline() -> None:
    with get_session() as db:
        leads = list_leads(db)
        summaries = [lead_to_summary(lead).model_dump() for lead in leads]
    if summaries:
        df = pd.DataFrame(summaries)
        df["income"] = df["annual_income_amount"].apply(lambda x: f"${x:,}")
        st.dataframe(
            df[
                [
                    "id",
                    "full_name",
                    "contact_preference",
                    "specialty",
                    "career_stage",
                    "income",
                    "score_tier",
                    "email_sent",
                    "status",
                    "created_at",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No applications yet.")


def render_export() -> None:
    st.warning("PII/PHI exports require secure handling.")
    pii = st.checkbox("Include full PII/PHI", True)
    ts = datetime.now().strftime("%Y%m%d")
    with get_session() as db:
        leads = list_leads(db, limit=10_000)
        rows = leads_to_export_rows(leads, include_pii=pii)
    if not rows:
        st.info("No applications to export.")
        return
    df = pd.DataFrame(rows)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    st.download_button("CSV", csv_buf.getvalue(), f"mip_{ts}.csv", mime="text/csv")
    st.download_button(
        "Excel",
        xlsx_buf.getvalue(),
        f"mip_{ts}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_scoring() -> None:
    for item in get_scoring_criteria_for_display():
        with st.expander(item["label"]):
            st.dataframe(
                pd.DataFrame([{"opt": k, "pts": v} for k, v in item["weights"].items()]),
                hide_index=True,
            )


def render_crm_page() -> None:
    page = st.session_state.get("crm_page", "Analytics")
    with st.sidebar:
        st.title("Admin CRM")
        st.caption("Application pipeline & analytics")
        page = st.radio(
            "Nav",
            ["Analytics", "Pipeline", "Application", "Export", "Scoring"],
            index=["Analytics", "Pipeline", "Application", "Export", "Scoring"].index(page),
            label_visibility="collapsed",
            key="crm_nav",
        )
        st.session_state["crm_page"] = page
        st.divider()
        st.page_link("app.py", label="Home")
        st.page_link("pages/Apply.py", label="Public Apply Form")

    if page == "Analytics":
        render_analytics()
    elif page == "Pipeline":
        render_pipeline()
    elif page == "Application":
        lid = st.number_input("Application ID", min_value=1, step=1)
        if st.button("Load", type="primary"):
            try:
                render_application_detail(_lead_dict(int(lid)))
            except ValueError as exc:
                st.error(str(exc))
    elif page == "Export":
        render_export()
    elif page == "Scoring":
        render_scoring()