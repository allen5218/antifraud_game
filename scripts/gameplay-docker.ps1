param(
    [ValidateSet('up','status','down','test')][string]$Action='up',
    [ValidatePattern('^[a-z][a-z0-9-]{2,45}$')][string]$ProjectName='scamgym-gameplay-v1',
    [int]$FrontendPort=17173,[int]$ApiPort=20000,[int]$SupabasePort=15621,[int]$MailPort=11380,
    [switch]$NoCache
)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$stateRoot=Join-Path $env:LOCALAPPDATA ('ScamGym\'+$ProjectName)
New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null
$buildRoot=$repoRoot
if($repoRoot -match '[^\x00-\x7F]'){
    $sha=[Security.Cryptography.SHA256]::Create()
    $shortHash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($repoRoot)))).Replace('-','').Substring(0,12)
    $aliasParent=Join-Path $env:LOCALAPPDATA 'ScamGym\workspaces'
    New-Item -ItemType Directory -Force -Path $aliasParent | Out-Null
    $buildRoot=Join-Path $aliasParent $shortHash
    if(Test-Path -LiteralPath $buildRoot){
        $item=Get-Item -LiteralPath $buildRoot -Force
        if($item.LinkType -ne 'Junction' -or @($item.Target)[0] -ne $repoRoot){throw 'Docker 建置別名已被其他資料使用。'}
    }else{New-Item -ItemType Junction -Path $buildRoot -Target $repoRoot | Out-Null}
}
if(-not (Get-Command node -ErrorAction SilentlyContinue)){throw '找不到 Node.js，請先安裝 Node.js 20 以上版本。'}
& node (Join-Path $PSScriptRoot 'prepare-gameplay-docker.cjs') $stateRoot $ProjectName $buildRoot $FrontendPort $ApiPort $SupabasePort $MailPort
if($LASTEXITCODE -ne 0){throw '環境設定產生失敗。'}
$compose=Join-Path $stateRoot 'compose.json'
function Invoke-GameCompose([string[]]$Arguments){
    & docker compose -p $ProjectName -f $compose @Arguments
    if($LASTEXITCODE -ne 0){throw 'Docker 操作失敗，請查看上方執行結果。'}
}
if($Action -eq 'down'){Invoke-GameCompose @('down');return}
if($Action -eq 'status'){Invoke-GameCompose @('ps');return}
if($Action -eq 'test'){
    Invoke-GameCompose @('run','--rm','backend-tests','uv','run','--no-sync','pytest','tests/','-q','-o','cache_dir=/tmp/pytest-cache','--junitxml=/artifacts/backend.xml')
    & node (Join-Path $PSScriptRoot 'gameplay-build-cache.cjs') check $stateRoot tests
    if($LASTEXITCODE -ne 0){
        Invoke-GameCompose @('build','frontend-tests','playwright')
        & node (Join-Path $PSScriptRoot 'gameplay-build-cache.cjs') record $stateRoot tests
        if($LASTEXITCODE -ne 0){throw '測試映像版本紀錄失敗。'}
    }
    Invoke-GameCompose @('run','--rm','--no-deps','frontend-tests','bun','test','src/')
    Invoke-GameCompose @('run','--rm','--no-deps','playwright','bunx','playwright','test','--config=playwright.gameplay.config.ts')
    return
}
& docker info --format '{{.OSType}}'
if($LASTEXITCODE -ne 0){throw '請先啟動 Docker Desktop。'}
$buildMatches=$false
if(-not $NoCache){
    & node (Join-Path $PSScriptRoot 'gameplay-build-cache.cjs') check $stateRoot
    $buildMatches=($LASTEXITCODE -eq 0)
}
if(-not $buildMatches){
    $buildArgs=@('build')
    if($NoCache){$buildArgs+='--no-cache'}
    $buildArgs+=@('prestart','frontend')
    Invoke-GameCompose $buildArgs
    & node (Join-Path $PSScriptRoot 'gameplay-build-cache.cjs') record $stateRoot
    if($LASTEXITCODE -ne 0){throw '建置版本紀錄失敗。'}
}
Invoke-GameCompose @('up','-d','--no-build','--wait','--wait-timeout','300')
$db=$ProjectName+'-db-1'
& docker exec $db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q -c 'CREATE TABLE IF NOT EXISTS scamgym_local_bootstrap (seed_key text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());'
if($LASTEXITCODE -ne 0){throw '資料庫初始化檢查失敗。'}
foreach($relative in @('deploy/seed/game_cases.sql','deploy/sql/2026-10-09-game-cases-pool.sql','deploy/sql/2026-10-16-exam-cases.sql')){
    $filename=Split-Path $relative -Leaf
    $applied=& docker exec $db psql -U postgres -d postgres -Atc "SELECT count(*) FROM scamgym_local_bootstrap WHERE seed_key='$filename';"
    if($LASTEXITCODE -ne 0){throw '題庫初始化紀錄讀取失敗。'}
    if($applied.Trim() -ne '1'){
        & docker cp (Join-Path $repoRoot $relative) ($db+':/tmp/'+$filename)
        if($LASTEXITCODE -ne 0){throw '題庫檔案傳入失敗。'}
        & docker exec $db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q -f ('/tmp/'+$filename)
        if($LASTEXITCODE -ne 0){throw '原始題庫匯入失敗。'}
        & docker exec $db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q -c "INSERT INTO scamgym_local_bootstrap(seed_key) VALUES ('$filename');"
        if($LASTEXITCODE -ne 0){throw '題庫初始化紀錄保存失敗。'}
    }
}
$testDbExists=& docker exec $db psql -U postgres -d postgres -Atc "SELECT count(*) FROM pg_database WHERE datname='scamgym_test';"
if($testDbExists.Trim() -eq '0'){
    & docker exec $db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q -c 'CREATE DATABASE scamgym_test;'
    if($LASTEXITCODE -ne 0){throw '獨立測試資料庫建立失敗。'}
}
Invoke-GameCompose @('run','--rm','backend-tests','uv','run','--no-sync','bash','scripts/prestart.sh')
$health=Invoke-RestMethod ('http://localhost:'+$ApiPort+'/api/v1/utils/health-check/')
if($health -ne $true){throw '後端健康檢查未通過。'}
$page=Invoke-WebRequest -UseBasicParsing ('http://localhost:'+$FrontendPort+'/')
if($page.StatusCode -ne 200){throw '前端未就緒。'}
& docker exec $db psql -U postgres -d postgres -Atc "SELECT pool,count(*) FROM game_cases WHERE status='published' GROUP BY pool ORDER BY pool;"
Write-Output ('遊戲已啟動：http://localhost:'+$FrontendPort)
Write-Output ('私密環境與資料庫設定保存在：'+$stateRoot)
