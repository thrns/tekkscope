# Use an official Python runtime as a parent image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libsqlcipher-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python3 -m playwright install --with-deps chromium

# Copy the rest of the application code
COPY . .

# The service does not need root privileges at runtime.
RUN useradd --create-home --uid 10001 appuser && \
    chown -R appuser:appuser /app /ms-playwright
USER appuser

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
