# Multi-stage Dockerfile for Databricks Delta Lake Project

# Stage 1: Base Python environment
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Stage 2: Development environment
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov black flake8 mypy isort

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Default command for development
CMD ["python", "-m", "pytest", "testing/", "-v"]

# Stage 3: Production environment
FROM base AS production

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import src.utils.common; print('Health check passed')" || exit 1

# Default command for production
CMD ["python", "scripts/main.py"]

# Stage 4: API service
FROM python:3.11-slim AS api

# Build arguments for environment configuration
ARG ENV_FILE=example.env
ARG ENVIRONMENT=dev

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=${ENVIRONMENT}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install lightweight API dependencies
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy source code
COPY src/ ./src/

# Create config directory structure and copy specified environment file
RUN mkdir -p ./config/environments
COPY config/environments/${ENV_FILE} ./config/environments/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for API
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 5: Data processing service
FROM base AS data-processing

# Build arguments for environment configuration
ARG ENV_FILE=example.env
ARG ENVIRONMENT=dev

# Set environment variable
ENV ENVIRONMENT=${ENVIRONMENT}

# Install additional data processing dependencies
RUN pip install --no-cache-dir pandas numpy scikit-learn

# Copy data processing code
COPY scripts/ ./scripts/
COPY src/ ./src/

# Create config directory structure and copy specified environment file
RUN mkdir -p ./config/environments
COPY config/environments/${ENV_FILE} ./config/environments/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Default command for data processing
CMD ["python", "scripts/data_processing/main.py"]
