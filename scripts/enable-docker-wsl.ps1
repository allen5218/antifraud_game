# 以系統管理員身分執行。只啟用 WSL 2 所需功能，不自動重新開機。
# Microsoft: https://learn.microsoft.com/windows/wsl/install-manual
$ErrorActionPreference = 'Stop'
$principal = [Security.Principal.WindowsPrincipal]::new(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw '請以系統管理員身分開啟 PowerShell，再執行此檔。'
}

$logDirectory = Join-Path (Split-Path -Parent $PSScriptRoot) '.codex\environment'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
Start-Transcript -Path (Join-Path $logDirectory 'windows-features.log') -Append
try {
    foreach ($featureName in @('VirtualMachinePlatform', 'Microsoft-Windows-Subsystem-Linux')) {
        $feature = Get-WindowsOptionalFeature -Online -FeatureName $featureName
        Write-Host ($featureName + ': ' + $feature.State)
        if ($feature.State -ne 'Enabled') {
            Enable-WindowsOptionalFeature -Online -FeatureName $featureName -All -NoRestart
        }
    }
    Write-Host 'Windows 功能設定完成。請儲存工作並自行重新開機，再啟動 Docker Desktop。'
    Write-Host '重開後：pwsh -File scripts/local-docker.ps1 up'
} finally {
    Stop-Transcript
}
