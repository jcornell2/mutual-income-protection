from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "Mutual Income Protection"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    encryption_key: str = ""
    admin_api_key: str = "dev-only-change-me"
    admin_passkey: str = "change-me-passkey"
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'leads.db'}"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_port: int = 8501
    data_retention_days: int = 365
    allowed_origins: str = "http://127.0.0.1:8501,http://localhost:8501"
    scoring_config_path: Path = BASE_DIR / "scoring_criteria.json"

    organization_name: str = APP_NAME
    organization_address: str = "Independent Disability Insurance Advisory"
    privacy_contact_email: str = "privacy@mutualincomeprotection.local"
    app_title: str = APP_NAME

    smtp_enabled: bool = True
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    alert_email_to: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    try:
        from frontend.secrets_bootstrap import _apply_streamlit_secrets

        _apply_streamlit_secrets()
    except Exception:
        pass
    return Settings()