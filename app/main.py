from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.rate_limit import limiter
from app.database import init_db
from app.routers import dashboard, exports, leads, templates

settings = get_settings()

app = FastAPI(
    title="Mutual Income Protection API",
    description="Disability insurance pre-application simulator — intake, AI scoring, CRM",
    version="4.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


STATIC = Path(__file__).parent / "static"


@app.get("/")
def landing_page():
    from fastapi.responses import HTMLResponse

    from frontend.html_pages import load_landing_html

    return HTMLResponse(load_landing_html())


@app.get("/apply")
def intake_form():
    return FileResponse(STATIC / "capture_form.html")


app.include_router(leads.router)
app.include_router(exports.router)
app.include_router(dashboard.router)
app.include_router(templates.router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. No sensitive data was logged."},
    )