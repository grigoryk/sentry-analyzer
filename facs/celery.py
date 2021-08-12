from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facs.settings')

app = Celery('facs')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    BROKER_URL=os.environ.get('REDIS_URL', 'amqp://guest:guest@localhost:5672/%2f'),
    CELERY_RESULT_BACKEND=os.environ.get('REDIS_URL', 'django-db')
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
