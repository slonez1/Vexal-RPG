FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files
COPY . /app

# Confirm that the FastAPI app is loaded
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
