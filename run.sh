#!/bin/bash

echo "Запуск SQL Challenge Backend..."

if [ ! -f .env ]; then
    echo "Создание .env файла из .env.example..."
    cp .env.example .env
    echo "⚠️  Не забудьте настроить .env файл с вашими ключами!"
fi

echo "Установка зависимостей..."
pip install -r requirements.txt

echo "Применение миграций..."
alembic upgrade head

echo "Запуск сервера..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
