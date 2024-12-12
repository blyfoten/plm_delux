# Use Python 3.11 as base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    graphviz \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/

# Create work directory
RUN mkdir /work

# Set environment variables
ENV PYTHONPATH=/app
ENV WORKSPACE_DIR=/work

# Expose port for FastAPI
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "src.web.backend.api:app", "--host", "0.0.0.0", "--port", "8000"] 