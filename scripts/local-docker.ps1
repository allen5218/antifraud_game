param(
    [ValidateSet('init', 'config', 'up', 'status', 'logs', 'down')]
    [string]$Action = 'up'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot '.env'
$composeRoot = $repoRoot

# BuildKit 的 session header 不接受中文路徑；junction 保留原專案位置與同一份檔案。
if ($repoRoot -match '[^\x00-\x7F]') {
    $aliasParent = Join-Path $env:LOCALAPPDATA 'ScamGym'
    $aliasPath = Join-Path $aliasParent 'workspace'
    New-Item -ItemType Directory -Force -Path $aliasParent | Out-Null
    if (Test-Path -LiteralPath $aliasPath) {
        $aliasItem = Get-Item -LiteralPath $aliasPath -Force
        if ($aliasItem.LinkType -ne 'Junction' -or @($aliasItem.Target)[0] -ne $repoRoot) {
            throw "Docker 路徑別名已被其他目錄使用：$aliasPath"
        }
    } else {
        New-Item -ItemType Junction -Path $aliasPath -Target $repoRoot | Out-Null
    }
    $composeRoot = $aliasPath
}

function Invoke-Compose {
    param([string[]]$ComposeArguments)
    & docker compose --project-directory $composeRoot --env-file (Join-Path $composeRoot '.env') `
        -p scamgym-local -f (Join-Path $composeRoot 'compose.yml') `
        -f (Join-Path $composeRoot 'compose.local.yml') @ComposeArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed (exit $LASTEXITCODE)."
    }
}

# 不覆寫既有設定；本機秘密僅寫入已被 Git 忽略的 .env。
if (-not (Test-Path -LiteralPath $envPath)) {
    $envContent = [IO.File]::ReadAllText((Join-Path $repoRoot '.env.example'))
    $localValues = [ordered]@{
        DOMAIN = 'localhost'
        FRONTEND_HOST = 'http://localhost:5173'
        ENVIRONMENT = 'local'
        SECRET_KEY = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
        FIRST_SUPERUSER = 'admin@example.com'
        FIRST_SUPERUSER_PASSWORD = ([guid]::NewGuid().ToString('N'))
        GOOGLE_API_KEY = ''
        POSTGRES_SERVER = 'localhost'
        POSTGRES_PORT = '54323'
        POSTGRES_DB = 'scamgym'
        POSTGRES_USER = 'postgres'
        POSTGRES_PASSWORD = ([guid]::NewGuid().ToString('N'))
        DOCKER_IMAGE_BACKEND = 'scamgym-local-backend'
        DOCKER_IMAGE_FRONTEND = 'scamgym-local-frontend'
        TAG = 'local'
        SMTP_HOST = 'mailcatcher'
        SMTP_PORT = '1025'
        SMTP_TLS = 'False'
        EMAILS_FROM_EMAIL = 'noreply@example.com'
    }
    foreach ($entry in $localValues.GetEnumerator()) {
        $envContent = [regex]::Replace(
            $envContent, '(?m)^' + [regex]::Escape($entry.Key) + '=.*\r?$',
            ($entry.Key + '=' + $entry.Value)
        )
    }
    [IO.File]::WriteAllText($envPath, $envContent, [Text.UTF8Encoding]::new($false))
    Write-Host '已建立本機 .env；管理員密碼請在該檔查看。'
}

switch ($Action) {
    'init' { Write-Host '本機設定已備妥。' }
    'config' { Invoke-Compose -ComposeArguments @('config', '--quiet') }
    'up' {
        & docker info --format '{{.OSType}}'
        if ($LASTEXITCODE -ne 0) {
            throw 'Docker 引擎尚未就緒。請先啟用 Virtual Machine Platform、重新開機並啟動 Docker Desktop。'
        }
        Invoke-Compose -ComposeArguments @('config', '--quiet')
        Invoke-Compose -ComposeArguments @('build', 'backend', 'frontend')
        Invoke-Compose -ComposeArguments @('up', '-d', '--no-build', '--wait', '--wait-timeout', '240')
        $dbUserLine = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^POSTGRES_USER=' } | Select-Object -Last 1
        $dbNameLine = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^POSTGRES_DB=' } | Select-Object -Last 1
        $dbUser = ($dbUserLine -replace '^POSTGRES_USER=', '').Trim().Trim('"', "'")
        $dbName = ($dbNameLine -replace '^POSTGRES_DB=', '').Trim().Trim('"', "'")
        Invoke-Compose -ComposeArguments @('exec', '-T', 'db', 'psql', '-U', $dbUser, '-d', $dbName, '-v', 'ON_ERROR_STOP=1', '-c', "SELECT 'published_cases' AS kind, count(*) FROM game_cases WHERE status='published' UNION ALL SELECT 'published_questions', count(*) FROM game_case_questions WHERE status='published';")
        $health = Invoke-RestMethod 'http://localhost:8000/api/v1/utils/health-check/'
        if ($health -ne $true) { throw '後端健康檢查未通過。' }
        $frontendResponse = Invoke-WebRequest -UseBasicParsing 'http://localhost:5173/'
        if ($frontendResponse.StatusCode -ne 200) { throw '前端未就緒。' }
        Write-Host '前後端健康檢查通過；題庫筆數請見上方。'
        Write-Host '網站：http://localhost:5173'
        Write-Host 'API：http://localhost:8000/docs'
        Write-Host '測試信箱：http://localhost:1080'
    }
    'status' { Invoke-Compose -ComposeArguments @('ps', '-a') }
    'logs' { Invoke-Compose -ComposeArguments @('logs', '--tail', '100') }
    'down' { Invoke-Compose -ComposeArguments @('down') }
}
