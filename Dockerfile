FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ ./backend/

# Copy frontend files
COPY frontend/ ./frontend/

# Environment variables
ENV PORT=8080
EXPOSE 8080

# Run the application from backend directory
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT
