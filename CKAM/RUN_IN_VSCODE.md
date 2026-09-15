# Run MandiWise in VS Code on Windows

## 1. Install prerequisites

Install these before opening the project:

- Python 3.11 (64-bit). During installation, enable **Add Python to PATH**.
- Node.js 20 LTS, which includes npm.
- Visual Studio Code.

Confirm them in a VS Code PowerShell terminal:

```powershell
py -3.11 --version
node --version
npm --version
```

## 2. Open the correct folder

Extract the ZIP, then in VS Code choose **File > Open Folder** and open the `CKAM` folder—the folder containing `backend`, `frontend`, `models`, and `mandiwise.db`.

## Recommended: automatic setup

Close any terminal that is already running `npm install`, then run this once from the `CKAM` folder:

```powershell
.\start_mandiwise.bat
```

The launcher uses Python 3.11 even if VS Code displays Python 3.14, repairs an incompatible `.venv`, installs one clean frontend dependency set, and only starts the servers after dependency checks pass. Do not run a separate `npm install` while this launcher is setting up.

## 3. Start the backend

Open a VS Code terminal in the `CKAM` folder and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Keep this terminal open. The API should be available at:

- http://127.0.0.1:8000/api/
- http://127.0.0.1:8000/docs

## 4. Start the frontend

In VS Code choose **Terminal > New Terminal**, then run:

```powershell
cd frontend
npm install
npm run dev
```

Keep this second terminal open and open:

- http://localhost:5173

## Faster manual start after first setup

On later runs, use these two terminals:

Backend:

```powershell
$env:PYTHONPATH = "$PWD\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

## Important notes

- Do not copy `.venv`, `venv`, or `frontend\node_modules` from another computer. Generate them locally using the commands above.
- `mandiwise.db`, the sample dataset, `price_model.joblib`, and `encoder.joblib` are already included. Do not retrain or repopulate them for a normal run.
- No `.env` file is required for local use.
- If port 5173 or 8000 is already in use, close the older MandiWise terminal before starting another server.
- If `py -3.11` is unavailable, reinstall Python 3.11 with the Python Launcher and PATH options enabled.
- Python 3.14 is not compatible with the versions of NumPy and scikit-learn pinned by this project. The automatic launcher downloads a project-private Python 3.11 copy when necessary.
- `npm WARN deprecated` messages are warnings, not failures. `npm ERR!` messages require attention.
- `TAR_ENTRY_ERROR` usually means two npm installs changed `node_modules` simultaneously. Stop both terminals and run only `start_mandiwise.bat` again.

## Verification commands

Backend tests, from the `CKAM` folder:

```powershell
$env:PYTHONPATH = "$PWD\backend"
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```
