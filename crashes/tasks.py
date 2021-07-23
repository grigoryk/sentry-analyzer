from celery import shared_task, chain
from .models import (
    AssignedCategory, Category, Event, EventGroup, EventTag, EventTagKeyed, Stacktrace,
    Project)

from django.db import IntegrityError
from django.core.cache import cache

import requests
import datetime

def events_endpoint_and_header(project):
    events_endpoint = project.events_endpoint_template % project.events_project_name
    return events_endpoint, {"Authorization": "Bearer " + project.token}

# Local processing:
@shared_task
def reset_processing(project_id):
    project = Project.objects.get(id=project_id)
    for s in Stacktrace.objects.filter(event__project=project, processed=True):
        s.processed = False
        s.save()

    Category.objects.filter(project=project).delete()
    AssignedCategory.objects.filter(group__project=project).delete()

@shared_task
def process_categories(project_id):
    project = Project.objects.get(id=project_id)
    for p in Category.objects.filter(project=project):
        process_category.delay(p.id)

@shared_task
def process_category(category_id):
    today = datetime.datetime.today()
    cutoff_date = today - datetime.timedelta(days=89)
    date_list = [(today - datetime.timedelta(days=x)).date() for x in range(90)]

    category = Category.objects.get(id=category_id)
    package = {
        "name": category.name,
        "dates": {d.isoformat(): {'info': 0, 'fatal': 0} for d in date_list}
    }
    for group in category.eventgroup_set.all():
        for event in group.event_set.filter(event_created__gte=cutoff_date):
            if event.is_info():
                package['dates'][event.event_created.date().isoformat()]['info'] += 1
            else:
                package['dates'][event.event_created.date().isoformat()]['fatal'] += 1
    cache.set('p_%s_computed_package_category_id_%s' % (category.project.id, category_id), package, None)

@shared_task
def process_stacktraces(project_id):
    project = Project.objects.get(id=project_id)
    for s in Stacktrace.objects.filter(event__project=project, processed=False):
        process_stacktrace.delay(s.id)

@shared_task
def process_stacktrace(stacktrace_id):
    s = Stacktrace.objects.get(id=stacktrace_id)
    mozilla_set = set()
    for line in s.stacktrace.split():
        if line.startswith("mozilla") or line.startswith("org.mozilla"):
            parts = line.split(".")
            package = ".".join((p for p in parts if not p[0].isupper() and p[0].isalpha()))
            mozilla_set.add(package)
            break
    for package in mozilla_set:
        # todo this can fail and produce cat=None
        try:
            cat = Category(project=s.event.project, name = package)
            cat.save()
        except IntegrityError:
            cat = Category.objects.filter(project=s.event.project, name = package).first()

        if AssignedCategory.objects.filter(group = s.event.group, category = cat).count() == 0:
            AssignedCategory(group = s.event.group, category = cat).save()

    s.processed = True
    s.save()

# Sentry integration:
@shared_task
def fetch_project(project_id):
    project = Project.objects.get(id=project_id)
    endpoint, headers = events_endpoint_and_header(project)

    r = requests.get(endpoint, headers=headers)
    r.raise_for_status()

    process_endpoint.delay(project_id, r.json())

    while "next" in r.links and r.links["next"]["results"] == "true":
        r = requests.get(r.links["next"]["url"], headers=headers)
        r.raise_for_status()
        process_endpoint.delay(project_id, r.json())

@shared_task
def process_endpoint(project_id, fetched_json):
    project = Project.objects.get(id=project_id)
    for e in fetched_json:
        # TODO these are hitting db locked
        group, _ = EventGroup.objects.get_or_create(project=project, group_id = e["groupID"])
        event, _ = Event.objects.get_or_create(
            project=project,
            group = group,
            event_id = e["eventID"],
            sentry_id = e["id"],
            defaults = {
                'event_received': e["dateReceived"],
                'event_created': e["dateCreated"],
                'message': e["message"]
            }
        )

        for tag in e["tags"]:
            if tag["key"] == "user":
                # too noisy
                continue

            event_tag, _ = EventTag.objects.get_or_create(project=project, key=tag["key"])

            try:
                keyed, _ = EventTagKeyed.objects.get_or_create(project=project, event_tag=event_tag, value=tag["value"])
                event.tags.add(keyed)
            except Exception:
                # we may be running into data races w/ celery running multiple tasks in parallel
                pass
        
        for entry in e["entries"]:
            if entry["type"] == "exception":
                for val in entry["data"]["values"]:
                    try:
                        frames = val["stacktrace"]["frames"]
                        stacktrace, created = Stacktrace.objects.get_or_create(
                            event=event,
                            stacktrace=format_stacktrace(frames)
                        )
                        if created:
                            process_stacktrace.delay(stacktrace.id)
                    except Exception:
                        pass

def format_stacktrace(frames):
    return "\n".join([f"{f['module']}#{f['function']}@{f['lineNo']}" for f in reversed(frames)])
