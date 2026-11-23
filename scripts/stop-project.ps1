[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path.TrimEnd('\')
$ProjectName = 'er-drekg-unified-staging'
$ComposeFile = Join-Path $ProjectRoot 'docker-compose.yml'

function Get-ListeningProcessId([int]$Port) {
    $line = netstat -ano -p tcp | Select-String -Pattern "127\.0\.0\.1:$Port\s+0\.0\.0\.0:0\s+LISTENING" | Select-Object -First 1
    if (-not $line) { return $null }
    return [int](($line.ToString().Trim() -split '\s+')[-1])
}

function Stop-ProjectListener([int]$Port, [string]$ExpectedPath, [string]$Description) {
    $listenerProcessId = Get-ListeningProcessId $Port
    if (-not $listenerProcessId) { Write-Output "$Description (port $Port) already stopped"; return }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$listenerProcessId"
    $parent = if ($process) { Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)" -ErrorAction SilentlyContinue }
    $matchesProject = $false
    foreach ($candidate in @($process, $parent)) {
        if (-not $candidate) { continue }
        foreach ($value in @($candidate.CommandLine, $candidate.ExecutablePath)) {
            if ($value -and $value.IndexOf($ExpectedPath, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $matchesProject = $true }
        }
    }
    if (-not $matchesProject) {
        throw "端口 $Port 的 PID $listenerProcessId 不属于 $ProjectRoot；为避免误停其他项目，已跳过。"
    }

    if ($parent -and $parent.CommandLine -and $parent.CommandLine.IndexOf($ExpectedPath, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and $parent.CommandLine -like '*uvicorn app.main:app*') {
        Stop-Process -Id $parent.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $listenerProcessId -Force -ErrorAction SilentlyContinue
    Write-Output "Stopped $Description (port $Port)"
}

Stop-ProjectListener 18083 (Join-Path $ProjectRoot 'backend\.venv') 'ER-DReKG API'
Stop-ProjectListener 15175 (Join-Path $ProjectRoot 'frontend\node_modules\vite') 'ER-DReKG frontend'

if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) { throw 'Docker CLI not found; app processes stopped but project databases were not stopped.' }
Push-Location $ProjectRoot
try {
    & docker compose --project-name $ProjectName -f $ComposeFile stop postgres neo4j
    if ($LASTEXITCODE -ne 0) { throw 'Failed to stop project PostgreSQL/Neo4j containers.' }
} finally {
    Pop-Location
}

Start-Sleep -Seconds 1
foreach ($port in @(18083, 15175, 5432, 7474, 7687)) {
    if (Get-ListeningProcessId $port) { Write-Warning "Port $port is still listening; inspect its process before stopping anything else." }
    else { Write-Output "Port $port closed" }
}
Write-Output 'Project containers are stopped; persistent data volumes are preserved.'
