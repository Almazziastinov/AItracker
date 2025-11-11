# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости (ffmpeg для обработки аудио)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл с зависимостями в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию
COPY . .

# Сообщаем Docker, что контейнер будет слушать этот порт
EXPOSE 8080

# Указываем команду для запуска бота при старте контейнера
CMD ["python", "telegram_bot/bot.py"]