from celery import shared_task
from .models import AssignedCategory, Category, Event, EventGroup, EventTag, EventTagKeyed, Stacktrace

from django.db import transaction, IntegrityError
from django.core.exceptions import MultipleObjectsReturned

import requests

ENDPOINT = "https://sentry.prod.mozaws.net/api/0"
EVENTS_ENDPOINT = ENDPOINT + "/projects/operations/fenix/events/"
TOKEN = "716efdd8ce4942eab62e31a18e29e44b0f5efa6e701747d1876b521a0466d2fc"
HEADERS = {"Authorization": "Bearer " + TOKEN}

# Local processing:
@shared_task
def assign_package_categories():
    for e in Event.objects.all():
        assign_package_categories_event.delay(e.id)

@shared_task
def assign_package_categories_event(event_id):
    event = Event.objects.get(id=event_id)
    for s in event.stacktrace_set.all():
        mozilla_set = set()
        for line in s.stacktrace.split():
            if line.startswith("mozilla") or line.startswith("org.mozilla"):
                parts = line.split(".")
                package = ".".join((p for p in parts if not p[0].isupper() and p[0].isalpha()))
                mozilla_set.add(package)
        for package in mozilla_set:
            try:
                cat = Category(name = package)
                cat.save()
            except IntegrityError:
                cat = Category.objects.filter(name = package).first()

            if AssignedCategory.objects.filter(group = event.group, category = cat).count() == 0:
                AssignedCategory(group = event.group, category = cat).save()


# Sentry integration:
@shared_task
def fetch_all():
    endpoint = EVENTS_ENDPOINT

    r = requests.get(endpoint, headers=HEADERS)
    r.raise_for_status()

    process_endpoint.delay(r.json())

    while "next" in r.links and r.links["next"]["results"] == "true":
        r = requests.get(r.links["next"]["url"], headers=HEADERS)
        r.raise_for_status()
        process_endpoint.delay(r.json())

@shared_task
def process_endpoint(fetched_json):
    for e in fetched_json:
        group, _ = EventGroup.objects.get_or_create(group_id = e["groupID"])
        event, _ = Event.objects.get_or_create(
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

            event_tag, _ = EventTag.objects.get_or_create(key=tag["key"])

            try:
                keyed, _ = EventTagKeyed.objects.get_or_create(event_tag=event_tag, value=tag["value"])
                event.tags.add(keyed)
            except Exception:
                # we may be running into data races w/ celery running multiple tasks in parallel
                pass
        
        for entry in e["entries"]:
            if entry["type"] == "exception":
                for val in entry["data"]["values"]:
                    try:
                        frames = val["stacktrace"]["frames"]
                        stacktrace, _ = Stacktrace.objects.get_or_create(
                            event=event,
                            stacktrace=process_stacktrace(frames)
                        )
                    except Exception:
                        pass

def process_stacktrace(frames):
    return "\n".join([f"{f['module']}#{f['function']}@{f['lineNo']}" for f in reversed(frames)])
