# MandiWise — one image, one URL.
# Stage 1: build the React frontend
FROM node:20-alpine AS web
WORKDIR /web
COPY CKAM/frontend/package.json CKAM/frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY CKAM/frontend/ ./
RUN npm run build

# Stage 2: run FastAPI and serve the built site + API
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/CKAM/backend

COPY CKAM/backend/requirements.txt /app/CKAM/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/CKAM/backend/requirements.txt

COPY CKAM/backend/ /app/CKAM/backend/
COPY CKAM/data/ /app/CKAM/data/
COPY CKAM/models/ /app/CKAM/models/
COPY --from=web /web/dist /app/CKAM/frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
