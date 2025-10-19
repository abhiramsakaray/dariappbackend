









FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and other requirements
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy application code (after installing requirements for better cache)
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Create uploads directory
RUN mkdir -p uploads

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Run database migrations automatically on container start
ENTRYPOINT ["/bin/bash", "-c", "alembic upgrade head && ./start.sh"]
