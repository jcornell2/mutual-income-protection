"""Write Streamlit Cloud secrets TOML from local .env (never commit the output)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
OUT_PATH = ROOT / "exports" / "streamlit-secrets.toml"

KEYS = [
    "ADMIN_PASSKEY",
    "ENCRYPTION_KEY",
    "DATABASE_URL",
    "SMTP_ENABLED",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM_EMAIL",
    "ALERT_EMAIL_TO",
    "ORGANIZATION_NAME",
]


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _toml_value(key: str, value: str) -> str:
    if key == "SMTP_ENABLED":
        return "true" if value.lower() in {"1", "true", "yes", "on"} else "false"
    if key == "SMTP_PORT":
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def main() -> None:
    env = _parse_env(ENV_PATH)
    missing = [key for key in KEYS if not env.get(key)]
    if missing:
        raise SystemExit(f"Missing in .env: {', '.join(missing)}")

    lines = [f"{key} = {_toml_value(key, env[key])}" for key in KEYS]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(lines)} keys)")
    print("Copy EVERY line (all keys) into Streamlit Cloud -> Settings -> Secrets.")
    print("Do NOT paste .env format (KEY=value). Use this TOML file exactly.")


if __name__ == "__main__":
    main()