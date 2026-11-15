FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_PORT=7860 \
    API_HOST=0.0.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-seed SQLite database
RUN python synth/generate_kb.py && \
    python synth/generate_customers.py && \
    python synth/generate_tickets.py && \
    PYTHONPATH=. python scripts/seed.py

EXPOSE 7860

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
