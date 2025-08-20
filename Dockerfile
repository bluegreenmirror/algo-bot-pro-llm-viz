FROM python:3.13-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove build-essential pkg-config \
 && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python","-m","src.app","--help"]
