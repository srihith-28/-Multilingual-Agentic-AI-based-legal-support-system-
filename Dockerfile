# ============================================================
# Stage 1: Build Frontend (Vite + React)
# ============================================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ============================================================
# Stage 2: Production Python Backend Runtime
# ============================================================
FROM python:3.11-slim AS runtime

# Install system dependencies (ffmpeg for audio handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application code
COPY backend/ ./backend/

# Copy built frontend assets into the directory where FastAPI expects them
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

# Default port for Render, Railway, Cloud Run
ENV PORT=8000
ENV APP_ENV=production
ENV APP_HOST=0.0.0.0

EXPOSE 8000

# Start Uvicorn bound to dynamic PORT
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
