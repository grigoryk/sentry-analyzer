release: python manage.py migrate
web: gunicorn facs.wsgi
worker: celery -A facs worker -l info
beat: celery -A facs beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
