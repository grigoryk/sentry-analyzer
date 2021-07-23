# sentry-analyzer
Experiments around analyzing sentry crashes

## Local usage, quick notes
- install and launch rabbitmq
- git clone && cd into project
- create python virtualenv: `python3 -m venv venv`
- activate it: `source venv/bin/activate`
- Install python libs: `pip install -r requirements.txt`
- Setup the local db: `./manage.py migrate` && `./manage.py createsuperuser`
- Set Sentry API token in `facs/crashes/tasks.py#TOKEN`
- Launch the app: `./manage.py runserver` and navigate to `http://127.0.0.1:8000/admin`
- Add the Sentry projects you care about via the Projects menu
- Endpoint template should be `https://sentry.prod.mozaws.net/api/0/projects/operations/%s/events/` for Mozilla projects
- Start-up celery tasks queue: `celery -A facs worker -l info`
- Kick-off the "fetch all" task via the django shell, for the project you want fetched (via its ID):
  - `./manage.py shell`
  - `>>> from crashes.tasks import fetch_project`
  - `>>> fetch_project.delay(1)`
- Once that's done, process its stacktraces and categorize data:
-   `>>> from crashes.tasks import process_stacktraces, process_categories`
-   `>>> process_stacktraces.delay(1)`
-   `>>> process_categories.delay(1)`
- Open the UI for you project: http://127.0.0.1:8000/crashes/1
