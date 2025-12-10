# Use a smaller, secure base image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m appuser

WORKDIR /app

# Install dependencies first (Caching layer)
COPY routers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Use list syntax for CMD and remove --reload for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

