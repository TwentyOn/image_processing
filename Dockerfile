FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    gcc \
    g++

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]