#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Database Backup Script
# ─────────────────────────────────────────────────────────────
BACKUP_DIR="./backups"
DB_FILE="./data/bot.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DIR/bot_$DATE.db"
    echo "✅ Backup created: $BACKUP_DIR/bot_$DATE.db"

    # Keep only last 30 backups
    ls -t "$BACKUP_DIR"/bot_*.db | tail -n +31 | xargs rm -f
    echo "🧹 Old backups cleaned"
else
    echo "❌ Database file not found: $DB_FILE"
    exit 1
fi
