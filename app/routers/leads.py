from fastapi import APIRouter, Depends, HTTPException, Request

from app.rate_limit import limiter
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    FollowUpCreate,
    FollowUpResponse,
    LeadCreate,
    LeadResponse,
    LeadSummary,
    LeadUpdate,
)
from app.services import (
    create_follow_up,
    create_lead,
    delete_lead,
    get_lead,
    lead_to_response,
    lead_to_summary,
    list_leads,
    update_lead,
)
from app.auth import require_admin_key

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", response_model=LeadResponse, status_code=201)
@limiter.limit("10/minute")
def submit_lead(request: Request, payload: LeadCreate, db: Session = Depends(get_db)):
    try:
        lead = create_lead(db, payload, actor="public_form", ip=request.client.host if request.client else None)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return lead_to_response(lead)


@router.get("", response_model=list[LeadSummary])
def get_leads(
    status: str | None = None,
    tier: str | None = None,
    provider_type: str | None = None,
    career_stage: str | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    leads = list_leads(
        db,
        status=status,
        tier=tier,
        provider_type=provider_type,
        career_stage=career_stage,
    )
    return [lead_to_summary(lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead_detail(lead_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin_key)):
    lead = get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead_to_response(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
def patch_lead(
    lead_id: int,
    payload: LeadUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    lead = get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    updated = update_lead(
        db,
        lead,
        payload,
        actor="admin_api",
        ip=request.client.host if request.client else None,
    )
    return lead_to_response(updated)


@router.delete("/{lead_id}", status_code=204)
def remove_lead(
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    lead = get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    delete_lead(db, lead, actor="admin_api", ip=request.client.host if request.client else None)


@router.post("/{lead_id}/follow-ups", response_model=FollowUpResponse, status_code=201)
def add_follow_up(
    lead_id: int,
    payload: FollowUpCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    lead = get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status == "unsubscribed":
        raise HTTPException(status_code=400, detail="Lead has unsubscribed from communications")

    try:
        follow_up = create_follow_up(
            db,
            lead,
            payload.template_key,
            custom_message=payload.custom_message,
            actor="admin_api",
            ip=request.client.host if request.client else None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return follow_up