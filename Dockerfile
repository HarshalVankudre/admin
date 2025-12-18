FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY api.py .
COPY dashboard.html .
# Copy logger if needed by API (api.py doesn't use logger, only reads DB)
# If api.py imports logger, we need it. Checking api.py... it imports psycopg2 directly.

# Environment variables
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
