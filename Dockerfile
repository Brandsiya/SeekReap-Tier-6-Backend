FROM python:3.11-slim

# Install system dependencies for PostgreSQL connectivity
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies from your existing requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn flask-cors

# Copy the entire backend source
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=True

# Port 8080 is the standard for Cloud Run
EXPOSE 8080

# Run with Gunicorn for production-grade concurrency
CMD exec gunicorn --bind :8080 --workers 2 --threads 4 --timeout 0 app:app
