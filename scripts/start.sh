#!/bin/bash

# Скрипт запуска системы мониторинга энергопотребления

echo "=== Запуск системы мониторинга энергопотребления ==="

# Проверка наличия Docker и Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p logs
mkdir -p docker/mysql/init
mkdir -p docker/mysql/conf

# Проверка наличия файлов конфигурации
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Файл docker-compose.yml не найден"
    exit 1
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск контейнеров
echo "🚀 Запуск контейнеров..."
docker-compose up -d --build

# Ожидание готовности MySQL
echo "⏳ Ожидание готовности MySQL..."
timeout=60
counter=0

while ! docker-compose exec mysql mysqladmin ping -h localhost --silent; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "❌ Таймаут ожидания MySQL"
        docker-compose logs mysql
        exit 1
    fi
    echo "Ожидание MySQL... ($counter/$timeout сек)"
done

echo "✅ MySQL готов"

# Проверка статуса контейнеров
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверка логов приложения
echo "📋 Последние логи приложения:"
docker-compose logs --tail=20 energy_app

echo ""
echo "🎉 Система запущена успешно!"
echo ""
echo "🌐 Веб-интерфейс: http://localhost:8080"
echo "🗄️  phpMyAdmin: http://localhost:8081"
echo ""
echo "📊 Для просмотра логов: docker-compose logs -f energy_app"
echo "🛑 Для остановки: docker-compose down"
echo ""
