#!/bin/bash

# Скрипт резервного копирования базы данных

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="energy_monitoring_backup_$DATE.sql"

echo "=== Создание резервной копии базы данных ==="

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Создание дампа базы данных
echo "📦 Создание дампа базы данных..."
docker-compose exec mysql mysqldump -u energy_user -penergy_password_123 energy_monitoring > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Резервная копия создана: $BACKUP_DIR/$BACKUP_FILE"
    
    # Сжатие бэкапа
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    echo "🗜️  Файл сжат: $BACKUP_DIR/$BACKUP_FILE.gz"
    
    # Удаление старых бэкапов (старше 30 дней)
    find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
    echo "🧹 Старые бэкапы удалены"
else
    echo "❌ Ошибка создания резервной копии"
    exit 1
fi
