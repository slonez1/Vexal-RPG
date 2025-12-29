# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps often needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better caching
COPY backend/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download spaCy model during image build (optional; remove if you want smaller image)
RUN python -m spacy download en_core_web_sm

# Copy backend and frontend into image (requires build context to be repo root)
COPY backend/ /app
COPY frontend/ /app/frontend

ENV PORT 8080
EXPOSE 8080

# Use uvicorn to run FastAPI main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
