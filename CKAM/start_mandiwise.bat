@echo off
setlocal EnableExtensions
title MandiWise Setup and Startup

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "LOCAL_TOOLS=%PROJECT_ROOT%\.tools"
set "LOCAL_PYTHON=%LOCAL_TOOLS%\python\tools\python.exe"
set "LOCAL_NODE=%LOCAL_TOOLS%\node"
set "VENV_DIR=%PROJECT_ROOT%\.venv"

echo ===================================================
echo MandiWise - safe Windows setup and startup
echo ===================================================
echo Run only this launcher. Do not run npm install in a
echo second terminal while setup is in progress.
echo.

call :find_python
if errorlevel 1 goto :failed
call :find_node
if errorlevel 1 goto :failed
call :setup_backend
if errorlevel 1 goto :failed
call :setup_frontend
if errorlevel 1 goto :failed

echo.
echo Starting the backend and frontend...
start "MandiWise Backend" cmd /k "cd /d ""%PROJECT_ROOT%"" && set ""PYTHONPATH=%PROJECT_ROOT%\backend"" && title MandiWise Backend Server && ""%VENV_DIR%\Scripts\python.exe"" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"
start "MandiWise Frontend" cmd /k "cd /d ""%PROJECT_ROOT%\frontend"" && title MandiWise Frontend Server && npm run dev"

echo Waiting for the servers to initialize...
ping 127.0.0.1 -n 6 >nul
echo.
echo ===================================================
echo MandiWise is ready at http://localhost:5173
echo Keep the Backend and Frontend windows open.
echo ===================================================
start "" http://localhost:5173
exit /b 0

:find_python
echo [1/4] Finding Python 3.11...
set "PYTHON_EXE="

if exist "%LOCAL_PYTHON%" (
    "%LOCAL_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=%LOCAL_PYTHON%"
)
if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('py -3.11 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%I"
)
if not defined PYTHON_EXE (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%I"
)
if not defined PYTHON_EXE (
    echo Python 3.11 was not found. Downloading a private portable copy...
    if not exist "%LOCAL_TOOLS%" mkdir "%LOCAL_TOOLS%"
    if not exist "%LOCAL_TOOLS%\python.zip" (
        curl.exe -L -o "%LOCAL_TOOLS%\python.zip" "https://www.nuget.org/api/v2/package/python/3.11.8"
        if errorlevel 1 (
            echo ERROR: Python download failed. Check your internet connection.
            exit /b 1
        )
    )
    if not exist "%LOCAL_PYTHON%" (
        powershell.exe -NoProfile -Command "Expand-Archive -Force -LiteralPath '%LOCAL_TOOLS%\python.zip' -DestinationPath '%LOCAL_TOOLS%\python'"
        if errorlevel 1 (
            echo ERROR: Python extraction failed.
            exit /b 1
        )
    )
    set "PYTHON_EXE=%LOCAL_PYTHON%"
)
"%PYTHON_EXE%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: MandiWise requires Python 3.11. Python 3.14 is not compatible with the pinned ML packages.
    exit /b 1
)
for /f "tokens=*" %%I in ('"%PYTHON_EXE%" --version 2^>^&1') do echo Using %%I
exit /b 0

:find_node
echo [2/4] Finding Node.js...
if exist "%LOCAL_NODE%\node.exe" set "PATH=%LOCAL_NODE%;%PATH%"
node --version >nul 2>&1
if errorlevel 1 (
    echo Node.js was not found. Downloading a private portable copy...
    if not exist "%LOCAL_TOOLS%" mkdir "%LOCAL_TOOLS%"
    if not exist "%LOCAL_TOOLS%\node.zip" (
        curl.exe -L -o "%LOCAL_TOOLS%\node.zip" "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
        if errorlevel 1 (
            echo ERROR: Node.js download failed. Check your internet connection.
            exit /b 1
        )
    )
    if not exist "%LOCAL_NODE%\node.exe" (
        powershell.exe -NoProfile -Command "Expand-Archive -Force -LiteralPath '%LOCAL_TOOLS%\node.zip' -DestinationPath '%LOCAL_TOOLS%\node_extract'"
        if errorlevel 1 (
            echo ERROR: Node.js extraction failed.
            exit /b 1
        )
        xcopy /E /Y /I "%LOCAL_TOOLS%\node_extract\node-v20.11.1-win-x64" "%LOCAL_NODE%" >nul
    )
    set "PATH=%LOCAL_NODE%;%PATH%"
)
node --version
call npm --version
if errorlevel 1 (
    echo ERROR: npm is unavailable.
    exit /b 1
)
exit /b 0

:setup_backend
echo [3/4] Setting up the Python backend...
cd /d "%PROJECT_ROOT%"
if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Replacing the incompatible or broken virtual environment...
        rmdir /s /q "%VENV_DIR%"
    )
)
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating a Python 3.11 virtual environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        exit /b 1
    )
)
echo Installing Python dependencies. This may take a few minutes...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: pip upgrade failed.
    exit /b 1
)
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%PROJECT_ROOT%\backend\requirements.txt"
if errorlevel 1 (
    echo ERROR: Backend dependency installation failed.
    exit /b 1
)
"%VENV_DIR%\Scripts\python.exe" -c "import fastapi, pandas, sklearn, uvicorn"
if errorlevel 1 (
    echo ERROR: Backend dependency verification failed.
    exit /b 1
)
set "PYTHONPATH=%PROJECT_ROOT%\backend"
if not exist "%PROJECT_ROOT%\models\price_model.joblib" "%VENV_DIR%\Scripts\python.exe" "%PROJECT_ROOT%\backend\scripts\train_ml.py"
if errorlevel 1 exit /b 1
if not exist "%PROJECT_ROOT%\models\encoder.joblib" "%VENV_DIR%\Scripts\python.exe" "%PROJECT_ROOT%\backend\scripts\train_ml.py"
if errorlevel 1 exit /b 1
if not exist "%PROJECT_ROOT%\mandiwise.db" "%VENV_DIR%\Scripts\python.exe" "%PROJECT_ROOT%\backend\scripts\populate_db.py"
if errorlevel 1 exit /b 1
exit /b 0

:setup_frontend
echo [4/4] Setting up the React frontend...
cd /d "%PROJECT_ROOT%\frontend"
if not exist "node_modules\.mandiwise-ready" (
    echo Installing a clean dependency set. Do not start another npm install.
    call npm ci
    if errorlevel 1 (
        echo ERROR: Frontend installation failed. Close other npm processes, then run this launcher again.
        exit /b 1
    )
    type nul > "node_modules\.mandiwise-ready"
)
node -e "require.resolve('vite'); require.resolve('lucide-react'); require.resolve('react')"
if errorlevel 1 (
    echo Frontend dependencies are incomplete. Repairing them...
    call npm ci
    if errorlevel 1 (
        echo ERROR: Frontend dependency repair failed.
        exit /b 1
    )
    type nul > "node_modules\.mandiwise-ready"
)
exit /b 0

:failed
echo.
echo ===================================================
echo SETUP STOPPED because an error occurred.
echo Read the ERROR line above, fix it, and run this file again.
echo No server was started with missing dependencies.
echo ===================================================
pause
exit /b 1
