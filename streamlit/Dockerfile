FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (create streamlit/requirements.txt or reference repo root requirements)
COPY streamlit_requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the app code (adjust paths if your streamlit files are at repo root)
COPY . /app

ENV PORT 8080
EXPOSE 8080

# Run streamlit server on the container port
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
