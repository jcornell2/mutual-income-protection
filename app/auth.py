from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_admin_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    settings = get_settings()
    if x_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key