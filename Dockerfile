# Multi-stage Dockerfile for Databricks Delta Lake Project

# Stage 1: Base Python environment
FROM python:3.11-slim as base

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
FROM base as development

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
FROM base as production

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import utils.common; print('Health check passed')" || exit 1

# Default command for production
CMD ["python", "scripts/main.py"]

# Stage 4: API service
FROM base as api

# Install API dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic

# Copy API code
COPY api/ ./api/
COPY utils/ ./utils/
COPY config/ ./config/

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
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 5: Data processing service
FROM base as data-processing

# Install additional data processing dependencies
RUN pip install --no-cache-dir pandas numpy scikit-learn

# Copy data processing code
COPY scripts/ ./scripts/
COPY utils/ ./utils/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Default command for data processing
CMD ["python", "scripts/data_processing/main.py"]
