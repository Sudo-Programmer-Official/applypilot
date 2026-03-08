# ApplyPilot

ApplyPilot is a resume-vs-job analysis MVP with a Vue frontend and FastAPI backend.

## Local development

Backend:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd apps/web
npm install
printf "VITE_API_BASE=http://localhost:8000\n" > .env
npm run dev
```

## Environment variables

Backend variables live in `apps/api/.env.example`.
Frontend variables live in `apps/web/.env.example`.
Production frontend base URL should be `https://api.tryapplypilot.com`.

## Deploy

Render:

- Blueprint config is in `render.yaml`.
- Service root directory is `apps/api`.
- Start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Set the custom domain to `api.tryapplypilot.com`.

Vercel:

- Set project root to `apps/web`.
- Build command: `npm run build`
- Output directory: `dist`
- SPA rewrites are configured in `apps/web/vercel.json` so deep links like `/dashboard/wizard` load on refresh.
- Set `VITE_API_BASE` to `https://api.tryapplypilot.com`.
- Connect `tryapplypilot.com` and `www.tryapplypilot.com`.

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`
