from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_admin_key
from app.schemas import DashboardStats
from app.scoring import get_scoring_criteria_for_display
from app.services import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), _: str = Depends(require_admin_key)):
    return get_dashboard_stats(db)


@router.get("/scoring-criteria")
def scoring_criteria(_: str = Depends(require_admin_key)):
    return get_scoring_criteria_for_display()