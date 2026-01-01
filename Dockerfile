# Base Python Image
FROM python:3.11-slim

# Set environment variables
ENV PORT=8080
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Server setup
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
