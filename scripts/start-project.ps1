[CmdletBinding()]
param(
    [switch]$OpenBrowser
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ProjectName = 'er-drekg-unified-staging'
$ApiPort = 18083
$FrontendPort = 15175
$ComposeFile = Join-Path $ProjectRoot 'docker-compose.yml'
$EnvFile = Join-Path $ProjectRoot '.env'
$BackendDirectory = Join-Path $ProjectRoot 'backend'
$FrontendDirectory = Join-Path $ProjectRoot 'frontend'
$Python = Join-Path $BackendDirectory '.venv\Scripts\python.exe'
$ViteEntry = Join-Path $FrontendDirectory 'node_modules\vite\bin\vite.js'
$LogDirectory = Join-Path $ProjectRoot 'logs'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'

function Get-ListeningProcessId([int]$Port) {
    $line = netstat -ano -p tcp | Select-String -Pattern "127\.0\.0\.1:$Port\s+0\.0\.0\.0:0\s+LISTENING" | Select-Object -First 1
    if (-not $line) { return $null }
    return [int](($line.ToString().Trim() -split '\s+')[-1])
}

function Test-ProjectListener([int]$Port, [string]$ExpectedPath) {
    $listenerProcessId = Get-ListeningProcessId $Port
    if (-not $listenerProcessId) { return $false }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$listenerProcessId"
    $parent = if ($process) { Get-CimInstance Win32_Process -Filter "ProcessId=$($process.ParentProcessId)" -ErrorAction SilentlyContinue }
    foreach ($candidate in @($process, $parent)) {
        if (-not $candidate) { continue }
        foreach ($value in @($candidate.CommandLine, $candidate.ExecutablePath)) {
            if ($value -and $value.IndexOf($ExpectedPath, [StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
        }
    }
    throw "端口 $Port 已被其他进程占用（PID $listenerProcessId）。为避免启动到别的项目，已停止本次启动。"
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw '缺少根目录 .env。先复制 .env.example 为 .env，并填写 PostgreSQL/Neo4j 密码；智谱 API Key 用于启用 AI 解释。'
}
if (-not (Test-Path -LiteralPath $ComposeFile)) { throw '缺少 docker-compose.yml。' }
if (-not (Test-Path -LiteralPath $Python)) { throw '缺少 backend\.venv。请先按 README 安装后端依赖。' }
if (-not (Test-Path -LiteralPath $ViteEntry)) { throw '缺少 frontend\node_modules。请先在 frontend 执行 npm ci。' }
$requiredFiles = @(
    'backend\app\main.py', 'backend\app\bootstrap.py', 'backend\app\core\config.py',
    'backend\app\db.py', 'backend\app\models.py', 'backend\app\schemas.py',
    'backend\app\graph_repository.py', 'backend\app\evidence_matrix.py',
    'backend\app\kg06.py', 'backend\app\kg07.py', 'backend\app\s1_precomputed.py',
    'backend\app\s2_stability.py', 'backend\pyproject.toml', 'backend\uv.lock',
    'frontend\package.json', 'frontend\package-lock.json', 'frontend\src\main.tsx'
)
$missingFiles = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $_)) })
if ($missingFiles.Count -gt 0) {
    throw "项目源码不完整：$($missingFiles -join ', ')。请从 staging 项目根目录启动，不要从只含派生 main.py 的 KG 审阅包启动。"
}

$Environment = @{}
foreach ($line in Get-Content -LiteralPath $EnvFile) {
    if ($line -match '^\s*([^#\s][^=]*)=(.*)$') { $Environment[$Matches[1].Trim()] = $Matches[2].Trim() }
}
foreach ($name in @('POSTGRES_PASSWORD', 'NEO4J_PASSWORD')) {
    if ([string]::IsNullOrWhiteSpace($Environment[$name]) -or $Environment[$name] -match '^replace_') {
        throw ".env 中的 $name 尚未配置；请填写本机专用密码后重试。"
    }
}
if ($Environment['GRAPH_SOURCE'] -ne 'neo4j') {
    throw '.env 的 GRAPH_SOURCE 必须是 neo4j，才能启动本项目的完整图谱功能。'
}
$databaseUrl = [regex]::Match($Environment['DATABASE_URL'], '^postgresql\+psycopg://([^:]+):([^@]+)@([^/:]+):(\d+)/([^?]+)')
if (-not $databaseUrl.Success -or $databaseUrl.Groups[3].Value -ne '127.0.0.1' -or $databaseUrl.Groups[4].Value -ne '5432') {
    throw '.env 的 DATABASE_URL 应指向本项目 PostgreSQL：127.0.0.1:5432。'
}
$databasePassword = [uri]::UnescapeDataString($databaseUrl.Groups[2].Value)
if ($databasePassword -cne $Environment['POSTGRES_PASSWORD']) {
    throw '.env 中 DATABASE_URL 与 POSTGRES_PASSWORD 不一致。'
}
$neo4jUri = [regex]::Match($Environment['NEO4J_URI'], '^bolt://127\.0\.0\.1:7687/?$')
if (-not $neo4jUri.Success) { throw '.env 的 NEO4J_URI 应指向本项目 Neo4j：bolt://127.0.0.1:7687。' }
if ([string]::IsNullOrWhiteSpace($Environment['ZHIPU_API_KEY'])) {
    Write-Warning '未配置 ZHIPU_API_KEY；平台仍可运行，但 AI 机制解释不可用。'
}

$null = Test-ProjectListener $ApiPort (Join-Path $BackendDirectory '.venv')
$null = Test-ProjectListener $FrontendPort (Join-Path $FrontendDirectory 'node_modules\vite')

$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if (-not $docker) { throw '未找到 Docker CLI。请启动 Docker Desktop 后重试。' }
& docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop 未就绪。请启动 Docker Desktop 后重试。' }

New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
$BackendStdout = Join-Path $LogDirectory "project-api-$Stamp.stdout.log"
$BackendStderr = Join-Path $LogDirectory "project-api-$Stamp.stderr.log"
$FrontendStdout = Join-Path $LogDirectory "project-vite-$Stamp.stdout.log"
$FrontendStderr = Join-Path $LogDirectory "project-vite-$Stamp.stderr.log"

Push-Location $ProjectRoot
try {
    & docker compose --project-name $ProjectName -f $ComposeFile up -d --wait --wait-timeout 120 postgres neo4j
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL/Neo4j 启动失败；请检查 Docker Desktop 与 Compose 日志。' }
} finally {
    Pop-Location
}

Push-Location $BackendDirectory
try {
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw '数据库迁移失败；后端和前端尚未启动。' }
} finally {
    Pop-Location
}

if (-not (Test-ProjectListener $ApiPort (Join-Path $BackendDirectory '.venv'))) {
    Start-Process -FilePath $Python `
        -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$ApiPort") `
        -WorkingDirectory $BackendDirectory -WindowStyle Hidden `
        -RedirectStandardOutput $BackendStdout -RedirectStandardError $BackendStderr | Out-Null
}

$apiReady = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $projectList = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/v1/projects" -TimeoutSec 3
        if (@($projectList | Where-Object { $_.slug -eq 'erpos-gse42568' }).Count -gt 0) { $apiReady = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}
if (-not $apiReady) { throw "后端在等待时间内未就绪。日志：$BackendStdout / $BackendStderr" }

if (-not (Test-ProjectListener $FrontendPort (Join-Path $FrontendDirectory 'node_modules\vite'))) {
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    if (-not $node) { throw '未找到 node.exe。请安装 Node.js 后重试。' }
    Start-Process -FilePath $node.Source `
        -ArgumentList @($ViteEntry, '--host', '127.0.0.1', '--port', "$FrontendPort", '--strictPort') `
        -WorkingDirectory $FrontendDirectory -WindowStyle Hidden `
        -RedirectStandardOutput $FrontendStdout -RedirectStandardError $FrontendStderr | Out-Null
}

$frontendReady = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort/" -TimeoutSec 3 -UseBasicParsing
        if ($response.StatusCode -eq 200) { $frontendReady = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}
if (-not $frontendReady) { throw "前端在等待时间内未就绪。日志：$FrontendStdout / $FrontendStderr" }

Write-Output 'ER-DReKG unified staging 已启动。'
Write-Output "前端：http://127.0.0.1:$FrontendPort"
Write-Output "后端 API：http://127.0.0.1:$ApiPort"
Write-Output "API 文档：http://127.0.0.1:$ApiPort/docs"
Write-Output "启动日志：$LogDirectory"
if ($OpenBrowser) { Start-Process "http://127.0.0.1:$FrontendPort" }
