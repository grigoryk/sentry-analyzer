release: ./release-tasks.py
web: gunicorn facs.wsgi
worker: celery -A facs worker
