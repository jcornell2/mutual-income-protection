from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_admin_key
from app.email_templates import list_templates, render_template
from app.schemas import EmailTemplatePreview

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/email", response_model=list[EmailTemplatePreview])
def get_email_templates(_: str = Depends(require_admin_key)):
    return [
        EmailTemplatePreview(key=t.key, name=t.name, subject=t.subject, body=t.body)
        for t in list_templates()
    ]


@router.get("/email/{template_key}/preview", response_model=EmailTemplatePreview)
def preview_email_template(template_key: str, _: str = Depends(require_admin_key)):
    try:
        rendered = render_template(
            template_key,
            first_name="Smith",
            specialty="Internal Medicine",
            career_stage="new_attending",
            place_of_work="Springfield Medical Center",
            work_state="IL",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EmailTemplatePreview(
        key=rendered.key,
        name=rendered.name,
        subject=rendered.subject,
        body=rendered.body,
    )