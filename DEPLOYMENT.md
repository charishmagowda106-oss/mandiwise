# Deploying MandiWise — one public URL

Target architecture — a **single Render web service** built from this repo's
`Dockerfile`:

| Piece        | Where it runs                                              |
| ------------ | ---------------------------------------------------------- |
| Website      | React build, served by FastAPI at `/`                      |
| API          | FastAPI at `/api/...` (same origin — no CORS setup needed) |
| Database     | Render free PostgreSQL, wired in via `DATABASE_URL`         |
| Live rates   | AGMARKNET (data.gov.in) with a fast daily-sync fallback     |

Local development is unchanged: `start_mandiwise_backend.bat` + `npm run dev`.

## 1. Push the code to GitHub

You need a free [GitHub](https://github.com) account. Create an **empty** repo
named `mandiwise` (no README, no license), then in PowerShell:

```powershell
cd C:\Users\USER\Desktop\mandiwisef
git add -A
git commit -m "MandiWise updates"   # only needed if `git status` shows changes
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mandiwise.git
git push -u origin main   # a browser window may pop up to sign in to GitHub
```

## 2. Create the site on Render

1. Sign up free at [render.com](https://render.com).
2. Dashboard → **New → Blueprint**.
3. Connect GitHub and select the `mandiwise` repository.
4. Render reads `render.yaml` from the repo root and proposes:
   - `mandiwise` — the web service (Docker)
   - `mandiwise-db` — free PostgreSQL, linked to `DATABASE_URL`
   - `SECRET_KEY` — generated automatically
5. Click **Apply** and wait for the first build (~5–10 min: npm install, vite
   build, pip install all happen inside Docker).

## 3. Open your website

You'll get a URL like `https://mandiwise-xxxx.onrender.com`. Share that link —
sign-up, GPS location, live rates, nearest mandis, profit ranking and price
prediction all work there (Render serves HTTPS, which browsers require for
geolocation).

On first boot the app seeds itself: **45 crops, 68 real Karnataka APMC mandis,
and the sample price history** (look for `[seed]` lines in Render's logs).

## Updating the site later

```powershell
cd C:\Users\USER\Desktop\mandiwisef
git add -A
git commit -m "describe the change"
git push
```
Render rebuilds and redeploys automatically.

## Notes & troubleshooting

- **Free tier sleep:** after ~15 min idle the service sleeps; waking takes
  ~30–60 s. (Live rates also wake the free mirror service on its first call.)
- **`DATA_GOV_API_KEY` (optional):** paste a data.gov.in key in
  Render → *Environment* if you have one; the public demo key is shared
  otherwise. Live rates work regardless via the mirror fallback.
- **`npm ci` fails in build:** make sure `CKAM/frontend/package-lock.json` is
  committed (`git add CKAM/frontend/package-lock.json`).
- **Crops/mandis show 0:** check Render logs for `[seed]` errors — usually a
  database permission problem; hit *Advanced → Clear build cache & deploy*.
- **Run the same stack locally with Docker:** `docker compose up --build`
  (see `docker-compose.yml`).
