from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import BASE_DIR, get_settings
from app.models import SCHEMA_VERSION, Base, SchemaMeta

settings = get_settings()
data_dir = BASE_DIR / "data"
data_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _current_schema_version() -> int | None:
    inspector = inspect(engine)
    if "schema_meta" not in inspector.get_table_names():
        return None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT version FROM schema_meta ORDER BY id DESC LIMIT 1")).fetchone()
        return row[0] if row else None


def init_db() -> None:
    version = _current_schema_version()
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    needs_reset = version != SCHEMA_VERSION
    if not needs_reset and "leads" in tables:
        columns = {col["name"] for col in inspector.get_columns("leads")}
        needs_reset = "contact_preference" not in columns

    if needs_reset and tables:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.query(SchemaMeta).count() == 0 or needs_reset:
            db.query(SchemaMeta).delete()
            db.add(SchemaMeta(version=SCHEMA_VERSION))
            db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()