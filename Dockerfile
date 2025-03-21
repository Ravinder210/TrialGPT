# Use Python 3.9 as base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy everything to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Command to run FastAPI server
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
