#booking/celery.py
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking.settings')

app = Celery('booking')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Add this line
app = app  # This ensures the app is shared across modules