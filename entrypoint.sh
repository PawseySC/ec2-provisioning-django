#!/bin/bash
set -e

# Wait for database to be ready
echo "Postgres is up - executing command"
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

# # Collect static files
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start supervisord
echo "Starting supervisord..."
exec supervisord -c /etc/supervisord.conf




