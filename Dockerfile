# Onion Quality AI — Root Dockerfile for Railway/Render
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for OpenCV (required for GrabCut)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend logic, ML models, and mobile web dist
COPY backend/ /app/backend/
COPY ml/ /app/ml/
COPY mobile/ /app/mobile/

# Set working directory to backend where the FastAPI app lives
WORKDIR /app/backend

EXPOSE 8000

# Run the FastAPI server
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
