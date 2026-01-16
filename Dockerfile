# Base image: Python slim version
FROM python:3.11-slim

# Set the working directory to the backend directory
WORKDIR /app/vexal-backend

# Copy the requirements file
COPY vexal-backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend directory into the image
COPY vexal-backend /app/vexal-backend

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Command to run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
