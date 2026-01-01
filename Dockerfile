# Base Python Image
FROM python:3.11-slim

# Set Environment Variables
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Add requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all app code
COPY . .

# Add PYTHONPATH for the app directory
ENV PYTHONPATH=/app

# Expose Streamlit default port
EXPOSE 8501

# Streamlit command to launch the app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
