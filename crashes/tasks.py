from celery import shared_task
from .models import Event, EventGroup, EventTag, EventTagKeyed, Stacktrace

import requests

ENDPOINT = "https://sentry.prod.mozaws.net/api/0"
EVENTS_ENDPOINT = ENDPOINT + "/projects/operations/fenix/events/"
TOKEN = "fd8f03e62b56422ea0a3a5cda26115d38d4f61fdfdc94df1a00ad9f7fd730459"
HEADERS = {"Authorization": "Bearer " + TOKEN}

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
