FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . /app

# Set explicit app directory and entry point
# Use PORT environment variable (Cloud Run sets this to 8080 by default)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--app-dir", "vexal-backend"]

