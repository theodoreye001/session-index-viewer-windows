param()

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerPath = Join-Path $RepoDir "server.py"
$StateDir = Join-Path $env:LOCALAPPDATA "session-index-viewer"
$PythonFile = Join-Path $StateDir "python.txt"
$PidFile = Join-Path $StateDir "server.pid"
$StdoutLog = Join-Path $StateDir "session-index-viewer.out.log"
$StderrLog = Join-Path $StateDir "session-index-viewer.err.log"

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Resolve-PythonExecutable {
    if (Test-Path $PythonFile) {
        $configured = (Get-Content $PythonFile -Raw).Trim()
        if ($configured -and (Test-Path $configured)) {
            return $configured
        }
    }

    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        $resolved = (& $py.Source -3 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1).Trim()
        if ($resolved -and (Test-Path $resolved)) {
            return $resolved
        }
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        $resolved = (& $python.Source -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1).Trim()
        if ($resolved -and (Test-Path $resolved)) {
            return $resolved
        }
    }

    throw "Python 3 was not found. Re-run install.ps1 after installing Python."
}

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

if (Test-Path $PidFile) {
    $existingText = (Get-Content $PidFile -Raw).Trim()
    $existingPid = 0
    if ([int]::TryParse($existingText, [ref]$existingPid)) {
        if (Test-ViewerProcess $existingPid) {
            exit 0
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $ServerPath)) {
    throw "server.py was not found at $ServerPath"
}

$Python = Resolve-PythonExecutable
$serverArgument = '"' + $ServerPath + '"'
$process = Start-Process `
    -FilePath $Python `
    -ArgumentList @("-u", $serverArgument) `
    -WorkingDirectory $RepoDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -PassThru

Set-Content -Path $PidFile -Value $process.Id -Encoding ASCII

try {
    $process.WaitForExit()
    exit $process.ExitCode
}
finally {
    if (Test-Path $PidFile) {
        $current = (Get-Content $PidFile -Raw).Trim()
        if ($current -eq [string]$process.Id) {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        }
    }
}
