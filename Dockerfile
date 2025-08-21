# Logan Dashboard - Multi-platform Docker Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="falkoro" \
      description="Logan Dashboard - Modern 1080p optimized Docker management interface" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/falkoro/logan" \
      org.opencontainers.image.description="Real-time Docker container management with SSH integration" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    PORT=5000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dashboard && \
    chown -R dashboard:dashboard /app

# Create SSH directory with proper permissions
RUN mkdir -p /home/dashboard/.ssh && \
    chmod 700 /home/dashboard/.ssh && \
    chown dashboard:dashboard /home/dashboard/.ssh

# Copy application code
COPY --chown=dashboard:dashboard . .

# Switch to non-root user
USER dashboard

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application with optimized settings
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "120", "--max-requests", "1000", "--preload", "run:app"]
