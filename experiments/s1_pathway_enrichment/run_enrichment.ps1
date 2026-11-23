$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$envRoot = Join-Path $base 'r-env'
$env:R_HOME = Join-Path $envRoot 'lib\R'
$env:PATH = (Join-Path $envRoot 'Library\bin') + ';' + (Join-Path $envRoot 'Library\usr\bin') + ';' + (Join-Path $envRoot 'Scripts') + ';' + (Join-Path $env:R_HOME 'bin') + ';' + (Join-Path $env:R_HOME 'bin\x64') + ';' + $env:PATH
$rscript = Join-Path $envRoot 'Scripts\Rscript.exe'
$script = Join-Path $base 'run_enrichment.R'
$log = Join-Path $base 'run.log'
& $rscript $script *> $log
if ($LASTEXITCODE -ne 0) { throw "Enrichment failed with exit code $LASTEXITCODE. See $log" }
Write-Host "Enrichment completed. See $base\enrichment_report.md"
