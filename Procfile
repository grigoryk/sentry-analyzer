release: python manage.py migrate
web: gunicorn facs.wsgi
worker: celery -A facs worker -l info
