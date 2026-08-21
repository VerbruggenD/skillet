### Frontend build stage (Next.js)
FROM node:24-alpine AS frontend-builder
WORKDIR /workspace
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

### Final image (Python app + built frontend)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies (kept minimal)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
	&& rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better caching
COPY pyproject.toml uv.lock ./

# Upgrade pip and install runtime dependencies
RUN python -m pip install --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy alembic pydantic-settings

# Copy application code
COPY app ./app
COPY migrations ./migrations

# Copy built frontend from the builder stage
COPY --from=frontend-builder /workspace/.next ./frontend/.next
COPY --from=frontend-builder /workspace/public ./frontend/public

EXPOSE 8000

# Default command — expects an ASGI app at `app.main:app`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

