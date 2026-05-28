#!/bin/bash
# Redis 数据备份 - Linux/Mac
# 用法: bash scripts/redis-backup.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/../.redis-backups"
DATE=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FOLDER="$BACKUP_DIR/$DATE"
mkdir -p "$BACKUP_FOLDER"

# 从 docker-compose 读取 Redis 端口
REDIS_PORT=$(grep -oP '-\s*"?\K\d+(?=:6379")' "$SCRIPT_DIR/../docker-compose.yml" 2>/dev/null || echo "6379")

# 判断 Redis 在 Docker 还是本地
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q redis; then
    CONTAINER=$(docker ps --format '{{.Names}}' | grep redis | head -1)
    docker exec "$CONTAINER" redis-cli BGSAVE
    sleep 2
    docker cp "$CONTAINER:/data/dump.rdb" "$BACKUP_FOLDER/"
    docker cp "$CONTAINER:/data/appendonly.aof" "$BACKUP_FOLDER/" 2>/dev/null || true
else
    redis-cli -p "$REDIS_PORT" BGSAVE
    sleep 2
    cp /var/lib/redis/dump.rdb "$BACKUP_FOLDER/" 2>/dev/null || cp ./dump.rdb "$BACKUP_FOLDER/"
    cp /var/lib/redis/appendonly.aof "$BACKUP_FOLDER/" 2>/dev/null || cp ./appendonly.aof "$BACKUP_FOLDER/" 2>/dev/null || true
fi

# 保留最近 30 个备份
ls -1dt "$BACKUP_DIR"/*/ 2>/dev/null | tail -n +31 | xargs rm -rf 2>/dev/null || true

SIZE=$(du -sh "$BACKUP_FOLDER" 2>/dev/null | cut -f1)
echo "备份完成: $BACKUP_FOLDER ($SIZE)"
