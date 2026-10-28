# One-command MandiWise APK build.
#
#   .\build_apk.ps1                                  # API = your PC's LAN IP:8000 (same-Wi-Fi testing)
#   .\build_apk.ps1 -ApiBase https://your-app.onrender.com/api   # API = hosted backend (share anywhere)
#
# Output: CKAM\MandiWise-<version>.apk
param(
    [string]$ApiBase = ""
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

# --- Toolchain installed for this project (see APP.md) ---
$env:JAVA_HOME = Join-Path $env:LOCALAPPDATA 'Android\jdk21'
$env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# --- Pick the API the app will talk to ---
if (-not $ApiBase) {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.*' } |
        Select-Object -First 1).IPAddress
    if (-not $ip) { throw "No LAN IP found - pass -ApiBase explicitly" }
    $ApiBase = "http://${ip}:8000/api"
}
Write-Host "API base: $ApiBase"
$env:VITE_API_BASE_URL = $ApiBase

# --- Web bundle -> Android project ---
Push-Location (Join-Path $root 'frontend')
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "web build failed" }
npx cap sync android
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "cap sync failed" }
Pop-Location

# --- Native build ---
Push-Location (Join-Path $root 'frontend\android')
& .\gradlew.bat assembleDebug --console=plain
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { throw "gradle build failed ($code)" }

# --- Collect the APK ---
$version = (Select-String -Path (Join-Path $root 'frontend\package.json') -Pattern '"version":\s*"([^"]+)"').Matches[0].Groups[1].Value
$dest = Join-Path $root "MandiWise-$version.apk"
Copy-Item (Join-Path $root 'frontend\android\app\build\outputs\apk\debug\app-debug.apk') $dest -Force
Write-Host "`nAPK ready to share: $dest"
