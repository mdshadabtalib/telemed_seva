# ── TeleMed Seva — Production Dockerfile ─────────────────────────────────────
# Multi-stage build: builder installs deps, runtime is lean.

FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install pre-built wheels (no compilation needed)
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application source
COPY . .

# Create upload directories
RUN mkdir -p uploads/avatars uploads/documents uploads/prescriptions \
              uploads/medicines uploads/reports logs

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Gunicorn starts the application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
