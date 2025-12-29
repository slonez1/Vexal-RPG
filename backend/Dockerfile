# backend/Dockerfile
FROM python:3.11-slim

# Set working directory to where the backend app lives inside the container
WORKDIR /app/backend

# Install system deps often needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better caching
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download spaCy model during image build (optional; remove if you want smaller image)
RUN python -m spacy download en_core_web_sm

# Copy the entire repository into /app (ensures frontend/ is included if present)
COPY . /app

ENV PORT 8080
EXPOSE 8080

# Run uvicorn from the backend working directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
