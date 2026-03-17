# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for cryptography and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' trader && \
    mkdir -p /app && \
    chown -R trader:trader /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY --chown=trader:trader src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER trader

# Default command
CMD ["python", "src/main.py"]
