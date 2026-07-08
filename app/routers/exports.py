import io
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_admin_key
from app.privacy import log_audit
from app.services import leads_to_export_rows, list_leads

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("/leads.csv")
def export_leads_csv(
    include_pii: bool = Query(True, description="Set false for anonymized export"),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    leads = list_leads(db, limit=10_000)
    rows = leads_to_export_rows(leads, include_pii=include_pii)
    if not rows:
        raise HTTPException(status_code=404, detail="No leads to export")

    df = pd.DataFrame(rows)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    log_audit(
        db,
        action="export",
        entity_type="lead",
        actor="admin_api",
        details=f"CSV export rows={len(rows)} include_pii={include_pii}",
    )

    filename = f"leads_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/leads.xlsx")
def export_leads_excel(
    include_pii: bool = Query(True, description="Set false for anonymized export"),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_key),
):
    leads = list_leads(db, limit=10_000)
    rows = leads_to_export_rows(leads, include_pii=include_pii)
    if not rows:
        raise HTTPException(status_code=404, detail="No leads to export")

    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    buffer.seek(0)

    log_audit(
        db,
        action="export",
        entity_type="lead",
        actor="admin_api",
        details=f"Excel export rows={len(rows)} include_pii={include_pii}",
    )

    filename = f"leads_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )