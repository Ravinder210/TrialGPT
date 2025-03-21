# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy only essential files
COPY backend.py requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt uvicorn

# Expose the port for FastAPI
EXPOSE 8000

# Run FastAPI server
CMD ["sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port ${PORT:-8000}"]
