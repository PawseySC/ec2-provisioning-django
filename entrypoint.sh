#!/bin/bash
set -e

# Wait for database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
    echo "Postgres is unavailable - sleeping"
    sleep 1
done

echo "Postgres is up - executing command"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Start supervisord
echo "Starting supervisord..."
exec supervisord -n -c /etc/supervisord.conf