param(
    [switch]$KeepLogs
)

$ErrorActionPreference = "Stop"

$TaskName = "Session Index Viewer"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerPath = Join-Path $RepoDir "server.py"
$StateDir = Join-Path $env:LOCALAPPDATA "session-index-viewer"
$PidFile = Join-Path $StateDir "server.pid"
$PythonFile = Join-Path $StateDir "python.txt"
$ModeFile = Join-Path $StateDir "install-mode.txt"
$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupLink = Join-Path $StartupDir "session-index-viewer.lnk"

function Test-ViewerProcess([int]$ProcessId) {
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
    }
    catch {
        return $false
    }
    if (-not $proc.CommandLine) {
        return $false
    }
    $fullServer = [IO.Path]::GetFullPath($ServerPath)
    return $proc.CommandLine.IndexOf(
        $fullServer,
        [StringComparison]::OrdinalIgnoreCase
    ) -ge 0
}

function Stop-ViewerProcess([int]$ProcessId) {
    if (Test-ViewerProcess $ProcessId) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        return $true
    }
    return $false
}

$stopped = $false
if (Test-Path $PidFile) {
    $pidText = (Get-Content $PidFile -Raw).Trim()
    $serverPid = 0
    if ([int]::TryParse($pidText, [ref]$serverPid)) {
        $stopped = Stop-ViewerProcess $serverPid
    }
}

if (-not $stopped) {
    try {
        $connections = Get-NetTCPConnection `
            -LocalAddress 127.0.0.1 `
            -LocalPort 7333 `
            -State Listen `
            -ErrorAction SilentlyContinue
        foreach ($processId in ($connections.OwningProcess | Sort-Object -Unique)) {
            if ($processId -and (Stop-ViewerProcess ([int]$processId))) {
                $stopped = $true
            }
        }
    }
    catch {
        # PID verification is best-effort. Do not kill an unverified process.
    }
}

if (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
}

if (Test-Path $StartupLink) {
    Remove-Item $StartupLink -Force
}

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Remove-Item $PythonFile -Force -ErrorAction SilentlyContinue
Remove-Item $ModeFile -Force -ErrorAction SilentlyContinue

if (-not $KeepLogs) {
    Remove-Item (Join-Path $StateDir "session-index-viewer.out.log") `
        -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $StateDir "session-index-viewer.err.log") `
        -Force -ErrorAction SilentlyContinue
}

if (Test-Path $StateDir) {
    $remaining = Get-ChildItem $StateDir -Force -ErrorAction SilentlyContinue
    if (-not $remaining) {
        Remove-Item $StateDir -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Uninstalled Session Index Viewer"
if ($stopped) {
    Write-Host "  server: stopped"
}
else {
    Write-Host "  server: no verified running process found"
}
if ($KeepLogs) {
    Write-Host "  logs:   kept in $StateDir"
}
