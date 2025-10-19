#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting DARI Wallet Backend V2..."

# Run database migrations
echo "📊 Running database migrations..."
alembic upgrade head

# Start the FastAPI application with uvicorn
echo "🔥 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
