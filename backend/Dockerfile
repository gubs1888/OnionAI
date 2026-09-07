# Onion Quality AI — backend image (kept deliberately simple)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

EXPOSE 8000

# Tables are created on startup (init_db) — safe on an empty database.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
