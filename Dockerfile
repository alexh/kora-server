FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start server with better logging
CMD gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-class=gthread \
    --worker-tmp-dir /dev/shm \
    --log-file=- \
    --log-level=debug \
    --pythonpath /app 