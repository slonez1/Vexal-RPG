# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps often needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model during image build (optional; can be removed if large)
RUN python -m spacy download en_core_web_sm

# Copy the rest of the backend files into the image
COPY . /app

ENV PORT 8080
EXPOSE 8080

# Use uvicorn to run FastAPI main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
