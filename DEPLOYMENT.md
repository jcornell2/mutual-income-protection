# Mutual Income Protection — Deployment Guide

Deploy the app as a **single Streamlit process**. Public visitors use the landing page and apply form; only `/Admin` requires a passkey.

## URL structure (recommended)

| Path | Page | Access |
|------|------|--------|
| `/` | Landing & overview | Public |
| `/Apply` | 8-step pre-application form | Public |
| `/Admin` | CRM, analytics, exports | Passkey required |

**Live app (Streamlit Cloud):**

- **https://cornell.streamlit.app/**

**Suggested app URL slug:** `cornell`

Share the public link: **`/`** for marketing, **`/Apply`** for direct intake (admin only).

---

## Prerequisites

1. **GitHub repo** with this project pushed (private recommended — contains business logic).
2. **Fernet encryption key** (generate once):
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. **Gmail app password** (if using email alerts): [Google App Passwords](https://myaccount.google.com/apppasswords)
4. **Strong admin passkey** — e.g. `openssl rand -hex 24` or a long random passphrase.

---

## Required secrets (all platforms)

| Variable | Purpose |
|----------|---------|
| `ADMIN_PASSKEY` | Admin CRM login (not shared publicly) |
| `ENCRYPTION_KEY` | Fernet key for PII at rest |
| `SMTP_USER` | Gmail address for alerts |
| `SMTP_PASSWORD` | Gmail app password |
| `SMTP_FROM_EMAIL` | Usually same as `SMTP_USER` |
| `ALERT_EMAIL_TO` | Where new-application emails go |
| `DATABASE_URL` | `sqlite:///./data/leads.db` (default) or Postgres URL |

Optional: `ORGANIZATION_NAME`, `SMTP_ENABLED`, `SMTP_HOST`, `SMTP_PORT`.

> **SQLite note:** On Streamlit Cloud, the filesystem is ephemeral — data resets on redeploy. For production persistence, use **Railway or Render with a persistent volume**, or point `DATABASE_URL` to managed Postgres.

---

## Local test (before deploying)

```bash
cd disability-lead-system
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # fill in secrets
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

- Home: http://localhost:8501/
- Apply: http://localhost:8501/Apply
- Admin: http://localhost:8501/Admin (passkey from `.env`)

---

## Option A — Streamlit Community Cloud (fastest, free)

**Links:** [share.streamlit.io](https://share.streamlit.io) · [Docs](https://docs.streamlit.io/streamlit-community-cloud)

### Steps

1. Push repo to GitHub.
2. Go to **https://share.streamlit.io** → **Create app**.
3. Select your repo, branch `main`.
4. **Main file path:** `frontend/app.py`
5. **App URL (optional):** `cornell`
6. Open **Advanced settings → Secrets** and paste (from `.streamlit/secrets.toml.example`, with real values):

```toml
ADMIN_PASSKEY = "your-strong-passkey"
ENCRYPTION_KEY = "your-fernet-key"
DATABASE_URL = "sqlite:///./data/leads.db"
SMTP_ENABLED = true
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "jacobcornell88@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
SMTP_FROM_EMAIL = "jacobcornell88@gmail.com"
ALERT_EMAIL_TO = "jacobcornell88@gmail.com"
ORGANIZATION_NAME = "Mutual Income Protection"
```

7. Click **Deploy**. First build takes ~3–5 minutes.

**Live URLs:**

- `https://cornell.streamlit.app/`
- `https://cornell.streamlit.app/Apply`
- `https://cornell.streamlit.app/Admin`

### Streamlit Cloud CLI (optional)

```bash
pip install streamlit
# After connecting GitHub in the UI, redeploys are automatic on git push.
git add . && git commit -m "Deploy MIP" && git push origin main
```

---

## Option B — Railway

**Links:** [railway.app](https://railway.app) · [Docs](https://docs.railway.app)

### Steps

1. Install CLI: `npm i -g @railway/cli` or use the web dashboard.
2. From project root:
   ```bash
   cd disability-lead-system
   railway login
   railway init
   ```
3. In Railway dashboard → **Variables**, add all secrets from the table above.
4. Set **Start command** (or use included `Procfile`):
   ```
   streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
   ```
5. **Persistent SQLite (recommended):** Add a volume mounted at `/app/data`, keep `DATABASE_URL=sqlite:///./data/leads.db`.
6. Deploy:
   ```bash
   railway up
   ```
7. **Settings → Networking → Generate domain** → e.g. `mutualincomeprotection.up.railway.app`

**Exact commands:**

```bash
cd C:\Users\jtcor\disability-lead-system
railway login
railway init
railway variables set ADMIN_PASSKEY="your-passkey" ENCRYPTION_KEY="your-fernet-key" SMTP_USER="you@gmail.com" SMTP_PASSWORD="app-password" ALERT_EMAIL_TO="you@gmail.com" SMTP_FROM_EMAIL="you@gmail.com"
railway up
railway domain
```

---

## Option C — Render

**Links:** [render.com](https://render.com) · [Docs](https://render.com/docs)

### Steps

1. Push repo to GitHub.
2. **Dashboard → New → Web Service** → connect repo.
3. Configure:
   - **Name:** `mutualincomeprotection`
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:**
     ```
     streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false
     ```
4. **Environment** → add all secrets (same as Streamlit Cloud).
5. **Disk (optional, for SQLite persistence):** Add disk, mount path `data`, size 1 GB.
6. Click **Create Web Service**.

**Live URL:** `https://mutualincomeprotection.onrender.com`

---

## Security checklist

- [ ] Change `ADMIN_PASSKEY` from default before going live.
- [ ] Generate a unique `ENCRYPTION_KEY`; never commit it.
- [ ] Do not share `/Admin` URL publicly; bookmark it for yourself.
- [ ] Use Gmail **app password**, not your main Google password.
- [ ] For HIPAA-sensitive production loads, consider Postgres + encrypted volume and a BAA with your host.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: app` | Run from repo root; `frontend/app.py` adds root to `sys.path`. |
| Admin passkey fails | Check `ADMIN_PASSKEY` in secrets/env matches exactly. |
| No email on submit | Verify `SMTP_*` vars; set `SMTP_ENABLED=true`. |
| Data lost after redeploy (Streamlit Cloud) | Expected with SQLite; use Railway/Render volume or Postgres. |
| Form submit does nothing | Ensure JavaScript is enabled; try Chrome. Check Streamlit logs for validation errors. |

---

## Local dual-mode (optional)

The original FastAPI + Streamlit launcher still works for local development:

```bash
python run.py
# or start.bat
```

- FastAPI landing: http://127.0.0.1:8000/
- Streamlit CRM: http://127.0.0.1:8501/

For cloud, use **`frontend/app.py`** only (no separate API process).