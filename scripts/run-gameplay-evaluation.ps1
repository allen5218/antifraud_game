param(
    [ValidatePattern('^[a-z][a-z0-9-]{2,45}$')][string]$ProjectName = 'scamgym-play-eval',
    [ValidatePattern('^[a-z][a-z0-9-]{0,23}$')][string]$RunName = ('verified-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$stateRoot = Join-Path $env:LOCALAPPDATA ('ScamGym\' + $ProjectName)
$metadataPath = Join-Path $stateRoot 'environment.json'
if (-not (Test-Path -LiteralPath $metadataPath)) { throw '請先使用 gameplay-docker.ps1 建立隔離環境。' }
$metadata = Get-Content -LiteralPath $metadataPath -Raw -Encoding UTF8 | ConvertFrom-Json
$runtimeRoot = Join-Path $metadata.runtime ('evaluation-' + $RunName)
if (Test-Path -LiteralPath $runtimeRoot) { throw '這個執行名稱已有資料，請換一個名稱以保留舊證據。' }
$inputRoot = Join-Path $runtimeRoot 'input'
$outputRoot = Join-Path $runtimeRoot 'output'
$reportRoot = Join-Path $repoRoot ('docs\agent-work\gameplay-evaluation\' + $RunName)
New-Item -ItemType Directory -Path $inputRoot, $outputRoot, $reportRoot -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot 'docs\agent-work\gameplay-evaluation\scripts\run-gameplay-eval.mjs') -Destination (Join-Path $inputRoot 'run-gameplay-eval.mjs')
$image = $ProjectName + '-playwright:gameplay-v1.1'
& docker image inspect $image --format '{{.Id}}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    & docker compose -p $ProjectName -f (Join-Path $stateRoot 'compose.json') build playwright
    if ($LASTEXITCODE -ne 0) { throw '評估映像建置失敗。' }
}
$passwordLine = Get-Content -LiteralPath (Join-Path $stateRoot 'supabase.env') -Encoding UTF8 | Where-Object { $_.StartsWith('POSTGRES_PASSWORD=') } | Select-Object -First 1
if (-not $passwordLine) { throw '找不到本機資料庫設定。' }
$previousPassword = [Environment]::GetEnvironmentVariable('PGPASS', 'Process')
$previousErrorPreference = $ErrorActionPreference
try {
    [Environment]::SetEnvironmentVariable('PGPASS', $passwordLine.Substring('POSTGRES_PASSWORD='.Length), 'Process')
    $apiUri = [Uri]$metadata.api
    $apiUrl = 'http://host.docker.internal:' + $apiUri.Port
    # Native stderr is retained as a log stream; the real process exit code
    # decides success, including on Windows PowerShell 5.1.
    $ErrorActionPreference = 'Continue'
    & docker run --rm --network ($ProjectName + '_default') --add-host=host.docker.internal:host-gateway `
        -e PGPASS -e ('EVAL_FRONTEND_URL=' + $metadata.website) -e ('EVAL_API_URL=' + $apiUrl) -e EVAL_OUT_DIR=/eval-output `
        -v ($inputRoot + ':/eval-input:ro') -v ($outputRoot + ':/eval-output') $image `
        sh -c ('cp /eval-input/run-gameplay-eval.mjs /app/frontend/run-gameplay-eval.mjs && /root/.bun/bin/bun /app/frontend/run-gameplay-eval.mjs ' + $RunName) `
        2>&1 | Tee-Object -FilePath (Join-Path $reportRoot 'execution.log')
    $evaluationExitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previousErrorPreference
    [Environment]::SetEnvironmentVariable('PGPASS', $previousPassword, 'Process')
    Get-ChildItem -LiteralPath $outputRoot -Force | Copy-Item -Destination $reportRoot -Recurse -Force
}
if ($evaluationExitCode -ne 0) { throw ('評估失敗，檢查點與失敗報告已保留在：' + $reportRoot) }
Write-Output ('評估完成，證據位置：' + $reportRoot)
