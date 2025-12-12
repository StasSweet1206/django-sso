FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Порт
EXPOSE 8000

# Команда запуска (БЕЗ миграций!)
CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn sso.wsgi:application --bind 0.0.0.0:$PORT
