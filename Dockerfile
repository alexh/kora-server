FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create migrations directory
RUN mkdir -p api/migrations && touch api/migrations/__init__.py

# Create log directory
RUN mkdir -p /var/log && touch /var/log/app.log && chmod 666 /var/log/app.log

# Command to run the application with logging
CMD uvicorn main:app --host 0.0.0.0 --port 8080 --proxy-headers --log-level debug --log-config /app/log_config.json 