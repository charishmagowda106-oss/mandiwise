# Registers the MandiWise relay task: every 4 hours, from this PC only.
#
#   powershell -ExecutionPolicy Bypass -File .github\scripts\register_pc_relay.ps1
#
# Runs only while the user is logged on (no stored password needed), starts
# as soon as possible after a missed slot (PC was asleep/off), tolerates
# battery power, and never overlaps with a still-running attempt.
# Hand-written XML because the PowerShell module cannot express an
# indefinite repetition (TimeSpan.MaxValue serializes out of range).

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)  # .github\scripts -> repo
$pythonw = Join-Path $repoRoot 'CKAM\.venv\Scripts\pythonw.exe'
$runner = Join-Path $PSScriptRoot 'pc_relay.py'
if (-not (Test-Path $pythonw)) { throw "pythonw not found: $pythonw" }
if (-not (Test-Path $runner)) { throw "runner not found: $runner" }

$start = (Get-Date).AddMinutes(10).ToString('yyyy-MM-ddTHH:mm:ss')

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>MandiWise: fetch data.gov.in Karnataka mandi prices and publish to the live-data branch</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>$start</StartBoundary>
      <Repetition>
        <Interval>PT4H</Interval>
      </Repetition>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$pythonw</Command>
      <Arguments>"$runner"</Arguments>
      <WorkingDirectory>$repoRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

Register-ScheduledTask -TaskName 'MandiWiseRelay' -Xml $xml -Force | Out-Null
Write-Output "Registered MandiWiseRelay - every 4 hours via $pythonw"
