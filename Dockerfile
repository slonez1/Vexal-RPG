FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . /app

# Set explicit app directory and entry point
ENTRYPOINT ["uvicorn", "--app-dir", "backend", "app:app", "--host", "0.0.0.0", "--port", "8080"]
