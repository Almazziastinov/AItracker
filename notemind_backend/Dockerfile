# Используем официальный базовый образ Python
FROM python:3.12-slim

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .

# Установка зависимостей. Убеждаемся, что установлены инструменты сборки для psycopg2/asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем весь остальной код проекта в рабочую директорию
COPY *.py .
COPY ./app /app/app

# Команда для запуска приложения
# Запускаем Uvicorn, указывая, что он слушает порт 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]