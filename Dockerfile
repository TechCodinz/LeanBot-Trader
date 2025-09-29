# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc6-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Create a non-root user
RUN useradd --create-home --shell /bin/bash leanbot
RUN chown -R leanbot:leanbot /app
USER leanbot

# Expose port for potential web interface
EXPOSE 8080

# Default command
CMD ["python", "main.py", "run"]