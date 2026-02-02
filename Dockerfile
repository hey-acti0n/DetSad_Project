# Единый образ приложения (фронтенд + бэкенд) для Docker Hub и запуска на ВМ
# Сборка для linux/amd64 (Yandex Cloud и большинство облаков)

# --- Сборка фронтенда ---
FROM --platform=linux/amd64 node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ENV NODE_ENV=production
RUN npm run build

# --- Финальный образ: бэкенд + статика фронтенда ---
FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN chmod +x entrypoint.sh

# Семенные данные из репозитория: при первом запуске (пустой том) копируются в /app/data
COPY backend/data /app/data_seed
ENV SEED_DATA_DIR=/app/data_seed

COPY --from=frontend-builder /app/dist /app/staticfiles

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
# --log-level error — только ошибки (не забивать диск логами на ВМ)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--log-level", "error", "config.wsgi:application"]
