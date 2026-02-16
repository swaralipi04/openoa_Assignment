# ─────────────────────────────────────────────────────────────
# OpenOA Backend — Production Dockerfile for GCP Cloud Run
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ gfortran libgeos-dev libproj-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────
# Final stage — slim runtime
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev libproj-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Copy cached example data (CSVs only, ~105 MB without zip)
COPY .data_cache/*.csv ./.data_cache/

# Cloud Run sets PORT env var — default to 8000
ENV PORT=8000

EXPOSE ${PORT}

# Use PORT env var so Cloud Run can assign its own port
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --timeout-keep-alive 120
