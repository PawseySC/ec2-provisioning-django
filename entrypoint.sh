#!/bin/bash
# entrypoint.sh

# Run database migrations
python manage.py migrate

# Start the Django development server
exec python manage.py runserver 0.0.0.0:8000
