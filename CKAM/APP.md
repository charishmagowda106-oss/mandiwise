# MandiWise as an APP

Two ways to experience MandiWise as an app, from "right now" to "real APK":

---

## 1. Today, on your phone (no install, ~1 minute)

The backend serves the built web app, so your phone just needs to be on the
**same Wi-Fi as your PC**.

1. Make sure the backend is running (it must listen on `0.0.0.0`, see below).
2. On your phone open **Chrome** and go to:

   ```
   http://192.168.0.110:8000
   ```

   *(replace `192.168.0.110` with your PC's current LAN IP — it changes when
   your network changes; check with `ipconfig`)*
3. Menu → **Add to Home screen** → it installs as a standalone app window
   (own icon, no browser bar) with offline shell support — that's the PWA layer:
   `frontend/public/manifest.webmanifest` + `sw.js`.

To start the backend on all interfaces:

```powershell
cd CKAM
$env:PYTHONPATH='backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

---

## 2. The real Android app (Capacitor) — built and ready to share

The native shell exists at **`CKAM/frontend/android/`** (app id
`com.mandiwise.app`), and the **build toolchain is already installed on this
PC**:

| Tool | Where |
|---|---|
| JDK 21 (Temurin) | `%LOCALAPPDATA%\Android\jdk21` |
| Android SDK (platform 36, build-tools 36, platform-tools) | `%LOCALAPPDATA%\Android\Sdk` |
| Android cmdline-tools | `%LOCALAPPDATA%\Android\Sdk\cmdline-tools\latest` |

(`JAVA_HOME`, `ANDROID_HOME` and the SDK paths are persisted as user
environment variables.)

### Build the APK (one command)
```powershell
cd CKAM
.\build_apk.ps1                 # API = your PC's LAN IP (same-Wi-Fi testing)
.\build_apk.ps1 -ApiBase https://your-app.onrender.com/api   # API = hosted backend
```
Output: **`CKAM\MandiWise-1.0.apk`** — already built once, so you can share
the existing file right now.

### Run it live in Android Studio (optional)
```powershell
cd CKAM\frontend
npm run app:open     # opens the project; press Run ▶ on emulator or USB device
```

### Sharing for reviews
- Send `MandiWise-1.0.apk` via WhatsApp / Drive / email. Reviewers tap it and
  allow **"Install from unknown sources"** when asked (standard for sideloaded
  APKs). Works on Android 7.0+.
- **The APK talks to your PC** (`http://192.168.0.110:8000/api` — baked in at
  build time), so reviewers must be on **your Wi-Fi** and your PC must be on
  with the backend running. That's ideal for family/house reviews.
- **For reviewers anywhere**: host the backend (the repo ships `render.yaml`
  for Render's free tier), then rebuild with
  `.\build_apk.ps1 -ApiBase https://<your-render-app>.onrender.com/api`.
  No other change needed.
- It's a **debug-signed** APK (fine for reviews). For a public release later,
  add a release keystore and build `assembleRelease`.

### Scripts added
| Script | What it does |
|---|---|
| `npm run app:sync` | `vite build` + copy bundle/config into `android/` |
| `npm run app:open` | open the Android project in Android Studio |
| `npm run dev:lan` | dev server exposed on your LAN (for phone testing) |

---

## How the pieces fit together

```
 ┌──────────── Android app (Capacitor WebView) ────────────┐
 │  bundled React build (same code as the website)         │
 │        │ fetch /api (VITE_API_BASE_URL)                 │
 └────────┼────────────────────────────────────────────────┘
          ▼
  FastAPI backend  :8000  ── SQLite/Postgres
   ├── /api/auth (password + phone OTP)
   ├── /api/alerts + /api/notifications
   └── background price-alert worker (every 2 min)
```

Everything the app does — OTP login, price alerts, the notification bell — is
plain REST, so the website and the Android app share **one backend and one
codebase**.

## Configuration notes

- **LAN IP changed?** Update `VITE_API_BASE_URL` (above) and
  `capacitor.config.json → android.allowNavigation`, then `npm run app:sync`.
- **Cleartext HTTP**: the debug build allows `http://` (LAN backend) via
  `android:usesCleartextTraffic="true"` in
  `frontend/android/app/src/main/AndroidManifest.xml`. For a Play Store
  release, serve the API over HTTPS instead and remove it.
- **SMS/Email delivery**: set `SMS_PROVIDER=twilio` (+ credentials) or
  `SMTP_HOST=...` in the server environment so OTPs and alerts really deliver —
  see `CKAM/.env.example`.
- **Production hosting**: deploy the backend (it already serves the web app)
  and point `VITE_API_BASE_URL` at it before `npm run app:sync`; then the app
  works on any network, no PC required.
