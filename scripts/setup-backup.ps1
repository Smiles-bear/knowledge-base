# Redis 自动备份配置 - Windows
# 用法: 以管理员身份运行 setup-backup.ps1
#       或在管理员 PowerShell 中: .\scripts\setup-backup.ps1

$ErrorActionPreference = "Stop"
$ScriptPath = "$PSScriptRoot\redis-backup.ps1"

if (-not (Test-Path $ScriptPath)) {
    Write-Host "错误: 找不到 redis-backup.ps1" -ForegroundColor Red
    pause; exit 1
}

# 创建 Windows 计划任务
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$taskName = 'KnowledgeBase-Redis备份'
Remove-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue -Confirm:$false
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings `
    -Description 'Knowledge Base 项目 Redis 每日备份（凌晨2点）'

Write-Host "自动备份已配置！" -ForegroundColor Green
Write-Host "  任务名称: $taskName"
Write-Host "  备份时间: 每天凌晨 2:00"
Write-Host "  备份位置: $PSScriptRoot\..\.redis-backups\"
Write-Host ""
Write-Host "管理命令:"
Write-Host "  taskschd.msc         # 打开任务计划程序查看"
Write-Host "  Get-ScheduledTask '$taskName'  # 查看任务状态"
Write-Host "  Unregister-ScheduledTask '$taskName'  # 删除自动备份"
