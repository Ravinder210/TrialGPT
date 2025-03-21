# Use official Python image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy only essential files (excluding large datasets/results)
COPY backend.py requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for FastAPI
EXPOSE 8000

# Run FastAPI server with dynamic port from Render
CMD ["sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port ${PORT:-8000}"]
