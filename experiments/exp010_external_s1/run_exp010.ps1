$ErrorActionPreference = 'Stop'
$expRoot = (Resolve-Path $PSScriptRoot).Path
$projectRoot = (Resolve-Path (Join-Path $expRoot '..\..')).Path
$rPrefix = Join-Path $projectRoot 'experiments\s1_pathway_enrichment\r-env'
$rHome = Join-Path $rPrefix 'lib\R'
$rscript = Join-Path $rPrefix 'Scripts\Rscript.exe'
$python = Join-Path $projectRoot 's2_lincs\.venv\Scripts\python.exe'
$logDir = Join-Path $expRoot 'logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
$env:R_HOME = $rHome
$env:PATH = (Join-Path $rHome 'bin\x64') + ';' + (Join-Path $rHome 'bin') + ';' + (Join-Path $rPrefix 'Library\bin') + ';' + (Join-Path $rPrefix 'Library\usr\bin') + ';' + $env:PATH
if (!(Test-Path $rscript)) { throw "Rscript missing: $rscript" }
if (!(Test-Path $python)) { throw "Python missing: $python" }
& $rscript --vanilla (Join-Path $expRoot 'scripts\run_exp010.R') ($projectRoot -replace '\\','/') 2>&1 | Tee-Object -FilePath (Join-Path $logDir 'limma_and_pathways.log')
if ($LASTEXITCODE -ne 0) { throw "R analysis failed with exit code $LASTEXITCODE" }
& $python -m pytest (Join-Path $expRoot 'tests') -q 2>&1 | Tee-Object -FilePath (Join-Path $logDir 'pytest.log')
if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }
& $python (Join-Path $expRoot 'scripts\complete_exp010.py') 2>&1 | Tee-Object -FilePath (Join-Path $logDir 'external_gsea_and_lincs.log')
if ($LASTEXITCODE -ne 0) { throw "External GSEA/LINCS scoring failed with exit code $LASTEXITCODE" }
Write-Output 'Exp010 completed; see results, figures, reports, and logs under the experiment folder.'
