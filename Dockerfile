FROM python:3.11-slim

# Установка зависимостей и supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor && \
    rm -rf /var/lib/apt/lists/*

# Копируем проект
WORKDIR /app
COPY . .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем конфиг для supervisord
COPY supervisord.conf /etc/supervisord.conf

# Запускаем supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
