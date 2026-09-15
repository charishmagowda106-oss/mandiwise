# MandiWise

MandiWise is a university demonstration app that helps farmers compare mandi returns and forecast crop prices. The React frontend calls a FastAPI backend, which uses SQLite market data and the included scikit-learn model.

## Included features

- JWT registration, login, current-user lookup, and protected frontend routes
- Crop and mandi data from SQLite
- Mandi ranking using latest stored price, Haversine distance, transport cost, and estimated selling return
- Price prediction using the included Random Forest model and encoder
- Responsive agricultural UI based on the supplied reference screens

The bundled price history is clearly labelled sample/demo data, not live market reporting. Predictions are estimates, not guaranteed prices.

## Windows setup (any folder)

### Prerequisites

- 64-bit Python 3.11 (recommended; Python 3.10–3.12 supported by the pinned packages)
- Node.js 18 or 20 LTS
- npm (included with Node.js)

Do not reuse a `venv` or `node_modules` folder copied from another computer. Virtual environments and native Node packages are machine-specific.

### Backend

Open PowerShell in the folder containing this README:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD\backend"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

API: http://127.0.0.1:8000/api/  
Interactive docs: http://127.0.0.1:8000/docs

### Frontend

Open a second PowerShell window in the same project folder:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

The Vite development server proxies `/api` to the backend. For a backend hosted elsewhere, create `frontend\.env` with:

```text
VITE_API_BASE_URL=http://server-address:8000/api
```

### Optional one-click start

Double-click `start_mandiwise.bat`. It resolves paths from its own location, creates a fresh `.venv`, installs missing dependencies, and starts both servers. Internet access is needed on the first run.

## Data and model files

- `mandiwise.db` is the included SQLite database. No database server is required.
- `models\price_model.joblib` and `models\encoder.joblib` are included and loaded by the real prediction endpoint.
- `data\sample\historical_prices.csv` is included demo data.
- Startup preserves the existing database and model files.

Only if those files are missing, regenerate them from the project folder:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python backend\scripts\train_ml.py
python backend\scripts\populate_db.py
```

## Configuration

No `.env` file is required for the local demo. Optional backend environment variables are:

- `SECRET_KEY`: JWT signing secret; change it outside a local demonstration.
- `DATABASE_URL`: SQLAlchemy database URL. The default is the project-root `mandiwise.db`.
- `CORS_ORIGINS`: comma-separated allowed frontend origins. The default allows local Vite URLs.

## Tests and production build

From the project folder with `.venv` activated:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m pytest backend\tests -q
cd frontend
npm run build
```

## Calculation rules

- 1 quintal = 100 kg
- Gross revenue = price per quintal × quantity in quintals
- Transport cost = Haversine distance in km × transport rate in ₹/km
- Estimated selling return = gross revenue − transport cost

Haversine distance is straight-line distance, not road distance. The included dataset is synthetic demo data and should be replaced with an official live source for production use.
