# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=100

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-client \
        curl \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r dashboarduser && \
    useradd -r -g dashboarduser -d /app -s /bin/bash dashboarduser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R dashboarduser:dashboarduser /app

# Switch to non-root user
USER dashboarduser

# Expose port
EXPOSE 100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:100/api/health || exit 1

# Run the application
CMD ["python", "run.py"]
