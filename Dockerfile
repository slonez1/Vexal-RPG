# Base Python Image
FROM python:3.11-slim

# Set environment variables
ENV PORT=8080
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose a port for the application
EXPOSE 8080

# Start the FastAPI application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
