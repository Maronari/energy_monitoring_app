#!/bin/bash

# Скрипт остановки системы мониторинга энергопотребления

echo "=== Остановка системы мониторинга энергопотребления ==="

# Остановка контейнеров
echo "🛑 Остановка контейнеров..."
docker-compose down

# Опционально: удаление volumes (раскомментируйте если нужно)
# echo "🗑️  Удаление данных..."
# docker-compose down -v

echo "✅ Система остановлена"
