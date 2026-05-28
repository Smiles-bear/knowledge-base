# Redis 数据备份 - Windows
# 用法: 右键运行，或 powershell -File scripts/redis-backup.ps1
param([string]$BackupDir = "$PSScriptRoot\..\.redis-backups")

$date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupFolder = "$BackupDir\$date"
New-Item -ItemType Directory -Force -Path $backupFolder | Out-Null

# 从 docker-compose 读取 Redis 端口，默认 6379
$redisPort = 6379
$composeFile = "$PSScriptRoot\..\docker-compose.yml"
if (Test-Path $composeFile) {
    $match = Select-String -Path $composeFile -Pattern 'redis.*?- "(\d+):6379"' | Select-Object -First 1
    if ($match) { $redisPort = [regex]::Match($match.Line, '(\d+):6379').Groups[1].Value }
}

# 连接 Redis 并触发保存
$redisCli = Get-Command redis-cli -ErrorAction SilentlyContinue
if (-not $redisCli) { $redisCli = "C:\Program Files\Redis\redis-cli.exe" }
else { $redisCli = $redisCli.Source }

& $redisCli -p $redisPort BGSAVE 2>$null
Start-Sleep -Seconds 3

# 复制备份文件
$redisDataDir = Split-Path $redisCli -Parent
Copy-Item "$redisDataDir\dump.rdb" -Destination "$backupFolder\" -Force -ErrorAction SilentlyContinue
Copy-Item "$redisDataDir\appendonly.aof" -Destination "$backupFolder\" -Force -ErrorAction SilentlyContinue

# 保留最近 30 个备份，删除旧的
$backups = Get-ChildItem -Path $BackupDir -Directory | Sort-Object Name -Descending
if ($backups.Count -gt 30) {
    $backups[30..($backups.Count - 1)] | Remove-Item -Recurse -Force
}

Write-Host "备份完成: $backupFolder ($((Get-ChildItem $backupFolder | Measure-Object Length -Sum).Sum) bytes)" -ForegroundColor Green
