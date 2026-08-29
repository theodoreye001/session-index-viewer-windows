param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

$TaskName = "Session Index Viewer"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunnerPath = Join-Path $RepoDir "run-windows.ps1"
$FrontendDir = Join-Path $RepoDir "frontend"
$StateDir = Join-Path $env:LOCALAPPDATA "session-index-viewer"
$PythonFile = Join-Path $StateDir "python.txt"
$ModeFile = Join-Path $StateDir "install-mode.txt"
$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupLink = Join-Path $StartupDir "session-index-viewer.lnk"
$PowerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

function Resolve-PythonExecutable {
    # Prefer the python.exe already selected by PATH. This respects active
    # environments and CI setup-python. Fall back to the Windows py launcher.
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        $output = & $python.Source -c "import sys; print(sys.executable)" 2>$null |
            Select-Object -First 1
        if ($output) {
            $resolved = ([string]$output).Trim()
            if ($resolved -and (Test-Path $resolved)) {
                return $resolved
            }
        }
    }

    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        $output = & $py.Source -3 -c "import sys; print(sys.executable)" 2>$null |
            Select-Object -First 1
        if ($output) {
            $resolved = ([string]$output).Trim()
            if ($resolved -and (Test-Path $resolved)) {
                return $resolved
            }
        }
    }

    throw "Python 3 was not found. Install Python 3 and re-run install.ps1."
}

function Test-ViewerHealthy {
    try {
        $response = Invoke-WebRequest `
            -Uri "http://127.0.0.1:7333/api/sessions?limit=1" `
            -UseBasicParsing `
            -TimeoutSec 1
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Build-FrontendBestEffort {
    if ($SkipFrontendBuild -or -not (Test-Path $FrontendDir)) {
        return
    }

    Push-Location $FrontendDir
    try {
        $bun = Get-Command bun.exe -ErrorAction SilentlyContinue
        $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if ($bun) {
            Write-Host "Building frontend with bun..."
            & $bun.Source install --frozen-lockfile
            if ($LASTEXITCODE -ne 0) { throw "bun install failed" }
            & $bun.Source run build
            if ($LASTEXITCODE -ne 0) { throw "bun run build failed" }
        }
        elseif ($npm) {
            Write-Host "Building frontend with npm..."
            & $npm.Source ci
            if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
            & $npm.Source run build
            if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
        }
        else {
            Write-Warning "bun/npm not found; the server will use sessions-index.html."
        }
    }
    catch {
        Write-Warning "Frontend build failed: $($_.Exception.Message)"
        Write-Warning "Installation will continue with the legacy viewer fallback."
    }
    finally {
        Pop-Location
    }
}

function Install-StartupShortcut {
    Write-Warning "Task Scheduler registration was unavailable; using the user Startup folder."
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($StartupLink)
    $shortcut.TargetPath = $PowerShellExe
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunnerPath`""
    $shortcut.WorkingDirectory = $RepoDir
    $shortcut.WindowStyle = 7
    $shortcut.Description = "Session Index Viewer"
    $shortcut.Save()
    Set-Content -Path $ModeFile -Value "startup" -Encoding ASCII
    return "startup"
}

if (-not (Test-Path $RunnerPath)) {
    throw "run-windows.ps1 was not found at $RunnerPath"
}
if (-not (Test-Path $PowerShellExe)) {
    $fallback = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if (-not $fallback) {
        throw "Windows PowerShell was not found."
    }
    $PowerShellExe = $fallback.Source
}

$Python = Resolve-PythonExecutable
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
Set-Content -Path $PythonFile -Value $Python -Encoding UTF8

Build-FrontendBestEffort

$installMode = $null
$scheduledTaskAvailable =
    (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue) -and
    (Get-Command New-ScheduledTaskAction -ErrorAction SilentlyContinue)

if ($scheduledTaskAvailable) {
    try {
        $userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $action = New-ScheduledTaskAction `
            -Execute $PowerShellExe `
            -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunnerPath`"" `
            -WorkingDirectory $RepoDir
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
        $principal = New-ScheduledTaskPrincipal `
            -UserId $userId `
            -LogonType Interactive `
            -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 1) `
            -ExecutionTimeLimit ([TimeSpan]::Zero) `
            -MultipleInstances IgnoreNew

        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Principal $principal `
            -Settings $settings `
            -Description "Local AI CLI session viewer on http://127.0.0.1:7333" `
            -Force | Out-Null

        # A previous fallback install may have left a Startup shortcut. Once
        # Task Scheduler succeeds, remove it so login cannot trigger twice.
        Remove-Item $StartupLink -Force -ErrorAction SilentlyContinue
        Set-Content -Path $ModeFile -Value "task" -Encoding ASCII
        $installMode = "task"
    }
    catch {
        Write-Warning "Task Scheduler registration failed: $($_.Exception.Message)"
        $installMode = Install-StartupShortcut
    }
}
else {
    $installMode = Install-StartupShortcut
}

if (-not (Test-ViewerHealthy)) {
    if ($installMode -eq "task") {
        Start-ScheduledTask -TaskName $TaskName
    }
    else {
        Start-Process `
            -FilePath $PowerShellExe `
            -ArgumentList @(
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", ('"' + $RunnerPath + '"')
            ) `
            -WorkingDirectory $RepoDir `
            -WindowStyle Hidden
    }

    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 250
        if (Test-ViewerHealthy) {
            break
        }
    }
}

Write-Host "Installed Session Index Viewer"
Write-Host "  mode:   $installMode"
Write-Host "  python: $Python"
Write-Host "  repo:   $RepoDir"
Write-Host "  state:  $StateDir"
Write-Host "  url:    http://127.0.0.1:7333"
if (Test-ViewerHealthy) {
    Write-Host "  status: running"
}
else {
    Write-Warning "The viewer is registered but did not answer on port 7333."
    Write-Warning "Check $StateDir\session-index-viewer.err.log"
}
