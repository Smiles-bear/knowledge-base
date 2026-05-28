#!/bin/bash
# Redis 自动备份配置 - Linux/Mac
# 用法: bash scripts/setup-backup.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/redis-backup.sh"

if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "错误: 找不到 redis-backup.sh"
    exit 1
fi

chmod +x "$BACKUP_SCRIPT"

CRON_LINE="0 2 * * * /bin/bash $BACKUP_SCRIPT >> $SCRIPT_DIR/../.redis-backups/cron.log 2>&1"
TMP_CRON=$(mktemp)
crontab -l 2>/dev/null | grep -v "redis-backup.sh" > "$TMP_CRON" || true
echo "$CRON_LINE" >> "$TMP_CRON"
crontab "$TMP_CRON"
rm "$TMP_CRON"

mkdir -p "$SCRIPT_DIR/../.redis-backups"

echo "自动备份已配置！"
echo "  备份时间: 每天凌晨 2:00"
echo "  备份位置: $SCRIPT_DIR/../.redis-backups/"
echo ""
echo "管理命令:"
echo "  crontab -l          # 查看定时任务"
echo "  crontab -e          # 编辑定时任务"
echo "  crontab -r          # 删除所有定时任务"
