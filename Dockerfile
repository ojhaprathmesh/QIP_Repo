# syntax=docker/dockerfile:1

# ==============================================================================
# Stage 1: Backend Builder (Python dependencies into isolated virtual env from uv.lock)
# ==============================================================================
FROM python:3.11-slim AS backend-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ==============================================================================
# Stage 2: Backend Runtime (FastAPI + Qiskit Quantum Simulator)
# ==============================================================================
FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

# Runtime shared libraries required by Qiskit Aer (OpenMP) and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 appgroup \
    && useradd --system --uid 1001 --gid appgroup --create-home appuser

COPY --from=backend-builder --chown=appuser:appgroup /app/.venv /opt/venv
COPY --chown=appuser:appgroup api/ ./api/
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup config/ ./config/
COPY --chown=appuser:appgroup data/ ./data/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]

# ==============================================================================
# Stage 3: Frontend Dependencies (Next.js)
# ==============================================================================
FROM node:20-alpine AS frontend-deps

WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

# ==============================================================================
# Stage 4: Frontend Builder (Next.js Standalone Production Build)
# ==============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/ui

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=frontend-deps /app/ui/node_modules ./node_modules
COPY ui/ ./

RUN npm run build

# ==============================================================================
# Stage 5: Frontend Runtime (Non-root Next.js Standalone Server)
# ==============================================================================
FROM node:20-alpine AS frontend

WORKDIR /app/ui

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0" \
    NEXT_PUBLIC_API_URL=http://localhost:8000

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=frontend-builder /app/ui/public ./public
COPY --from=frontend-builder --chown=nextjs:nodejs /app/ui/.next/standalone ./
COPY --from=frontend-builder --chown=nextjs:nodejs /app/ui/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
