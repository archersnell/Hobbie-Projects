param(
    [string]$TaskName = "Stock Tracker",
    [string]$ProjectRoot = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$pythonPath = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$mainPath = Join-Path $ProjectRoot "main.py"

if (-not (Test-Path $pythonPath)) {
    Write-Error "Could not find venv Python at $pythonPath"
    exit 1
}

if (-not (Test-Path $mainPath)) {
    Write-Error "Could not find main.py at $mainPath"
    exit 1
}

try {
    $action = New-ScheduledTaskAction `
        -Execute $pythonPath `
        -Argument "`"$mainPath`"" `
        -WorkingDirectory $ProjectRoot

    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Runs the Stock Tracker notification scheduler on login." `
        -Force

    Write-Host "Installed scheduled task: $TaskName"
    Write-Host "Run it now with: Start-ScheduledTask -TaskName `"$TaskName`""
}
catch {
    Write-Error "Could not install scheduled task '$TaskName'. Try running PowerShell as Administrator, then run this script again. Original error: $($_.Exception.Message)"
    exit 1
}
