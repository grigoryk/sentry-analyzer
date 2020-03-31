# sentry-analyzer
Experiments around analyzing sentry crashes

## Local usage, quick notes
- install and launch rabbitmq
- Install python libs: `pip install -r requirements.txt`
- Setup the local db: `./manage.py migrate` && `./manage.py createsuperuser`
- Set Sentry API token in `facs/crashes/tasks.py#TOKEN`
- Launch the app: `./manage.py runserver` and navigate to `http://127.0.0.1:8000/admin`
- Start-up celery tasks queue: `celery -A facs worker -l info`
- Kick-off the "fetch all" task via the django shell:
  - `./manage.py shell`
  - `>>> from crashes.tasks import fetch_all`
  - `>>> fetch_all.delay()`
