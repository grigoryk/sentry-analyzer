from celery import shared_task, chord, group
from .models import (
    AssignedCategory, Category, CategoryCount, ComputedTrend, Event, EventGroup, EventTag, EventTagKeyed, ProcessEventTag, Stacktrace,
    Project, ProjectEndpointCache)

from django.db import IntegrityError
from django.core.cache import cache

import requests
import datetime
import statsmodels.api as sm
import statistics
import pytz
import json

# TODO assignedcategory insert violations

@shared_task
def update_all_projects():
    for p in Project.objects.all():
        do_all_for_project(p.id)

def do_all_for_project(project_id):
    # chain:
    # - fetch_project
    # - chord: process_project_endpoints -> [process_endpoint_events...]
    # - chord: process_stacktraces -> [process_stacktrace...]
    # - process_project_counts
    # - process_project_trends

    chain = fetch_project.si(project_id) | process_project_endpoints.si(project_id) | process_stacktraces.si(project_id) | process_project_counts.si(project_id) | process_project_trends.si(project_id)
    chain()

def events_endpoint_and_header(project):
    events_endpoint = project.events_endpoint
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
def process_project_event_tag_counts(project_id):
    etks = set()
    for pet in ProcessEventTag.objects.filter(project__id=project_id):
        etks.update(list(EventTagKeyed.objects.filter(event_tag=pet.event_tag)))

    all_tasks = []
    for etk in etks:
        for c in Category.objects.filter(project__id=project_id):
            all_tasks.append(process_category_counts.si(c.id, etk.id))
    group(all_tasks)().get(disable_sync_subtasks=False)

@shared_task
def process_project_counts(project_id):
    group(
        [
            process_category_counts.si(c.id, None)
            for c in Category.objects.filter(project__id=project_id)
        ]
    )().get(disable_sync_subtasks=False)

@shared_task
def process_category_counts(category_id, etk_id):
    etk = None
    if etk_id:
        etk = EventTagKeyed.objects.get(id=etk_id)

    today = datetime.datetime.now().replace(tzinfo=pytz.UTC)
    cutoff_date = today - datetime.timedelta(days=89)
    date_list = [(today - datetime.timedelta(days=x)).date() for x in range(90)]

    category = Category.objects.get(id=category_id)
    dates = {d.isoformat(): {'info': 0, 'fatal': 0} for d in date_list}
    for group in category.eventgroup_set.filter(project=category.project):
        if etk:
            events = group.event_set.filter(event_created__gte=cutoff_date, tags__in=[etk])
        else:
            events = group.event_set.filter(event_created__gte=cutoff_date)
        for event in events:
            if event.is_info():
                dates[event.event_created.date().isoformat()]['info'] += 1
            else:
                dates[event.event_created.date().isoformat()]['fatal'] += 1

    for d in dates:
        CategoryCount.objects.update_or_create(
            category=category,
            date=d,
            keyed_tag=etk,
            defaults = {
                'info_count': dates[d]['info'],
                'fatal_count': dates[d]['fatal']
            }
        )

@shared_task
def process_project_trends(project_id):
    group(
        [
            process_category_trends.si(p.id)
            for p in Category.objects.filter(project__id=project_id)
        ]
    )().get(disable_sync_subtasks=False)

@shared_task
def process_category_trends(category_id):
    def reduce_regressions(fitted):
        diffs = []
        fitted_values = fitted.predict()
        #print("fitted_values: %s" % fitted_values)
        # 0 - today, 1 - yesterday, etc
        # so, collect deltas of predictions for yesterday to today, etc.
        for i, r in enumerate(fitted_values[:-1]):
            diffs.append(r - fitted_values[i + 1])
        #print("diffs: %s" % diffs)
        reduced = [
            round(statistics.mean(diffs[0:i]), 3)
            for i in range(1, len(diffs))
        ]
        #print("reduced: %s" % reduced)
        return reduced

    category = Category.objects.get(id=category_id)
    # except for today, likely to be incomplete
    cc = CategoryCount.objects.filter(category=category, keyed_tag=None).order_by('-date')[1:]
    latest_date = cc[0].date
    info_counts = [c.info_count for c in cc]
    fatal_counts = [c.fatal_count for c in cc]
    days = [d for d in range(0, cc.count())]

    #print("info counts: %s" % info_counts)
    info_reduced = reduce_regressions(sm.OLS(days, info_counts).fit())
    #print("fatal counts: %s" % fatal_counts)
    fatal_reduced = reduce_regressions(sm.OLS(days, fatal_counts).fit())

    for i in range(0, len(info_reduced)):
        ComputedTrend.objects.update_or_create(
            category=category,
            for_date=latest_date,
            days_back=i,
            defaults={
                'info_trend': info_reduced[i],
                'fatal_trend': fatal_reduced[i]
            }
        )

@shared_task
def process_stacktraces(project_id):
    project = Project.objects.get(id=project_id)
    group(
        [
            process_stacktrace.si(s['id'])
            for s in Stacktrace.objects.filter(event__project=project, processed=False).values('id')
        ]
    )().get(disable_sync_subtasks=False)

@shared_task
def process_stacktrace(stacktrace_id):
    s = Stacktrace.objects.select_related('event').get(id=stacktrace_id)
    mozilla_set = set()
    for line in s.stacktrace.split():
        if line.startswith("mozilla") or line.startswith("org.mozilla"):
            parts = line.split(".")
            package = ".".join((p for p in parts if not p[0].isupper() and p[0].isalpha()))
            mozilla_set.add(package)
            break
    for package in mozilla_set:
        cat, _ = Category.objects.get_or_create(project=s.event.project, name = package)
        AssignedCategory.objects.get_or_create(group = s.event.group, category = cat)

    s.processed = True
    s.save()

# Sentry integration:
@shared_task
def fetch_project(project_id):
    # figure out most recent event we have for the project
    # cutoff = most_recent - 5 days
    # process endpoint
    # figure out latest date present; if it's ahead of cutoff, continue
    # if there's a next endpoint, process it

    # how to make this parallel? by the time worker finished processing endpoint, it's free
    # to process another one
    # go get at endpoint+1, we have to fetch endpoint
    # so, endpoint fetching is serialized
    # so, may as well make it parallell over projects, not endpoints

    # the bottleneck isn't fetching but local processing (somewhat surprisingly).
    # so, try to minimize costs of that since it's serialized...

    # or: we fetch bunch of endpoints into a local cache until we get to the cutoff date
    # then we process what we fetched (parallel!)
    # then clear out the cache
    # this also provides clear look into what's going on w/ the system

    project = Project.objects.get(id=project_id)
    next_endpoint, headers = events_endpoint_and_header(project)

    newest_event = Event.objects.filter(project=project).order_by('-event_created').values('event_created').first()
    # if we have no data, fetched past three months.
    # otherwise, fetch missing data + 2 day overlap.
    if not newest_event:
        today = datetime.datetime.now().replace(tzinfo=pytz.UTC)
        cutoff_date = today - datetime.timedelta(days=90)
    else:
        # go back a bit more than we need to, just in case - it's possible to encounter out-of-order events
        newest_date = newest_event['event_created'].replace(tzinfo=pytz.UTC)
        cutoff_date = newest_date - datetime.timedelta(days=2)

    while True:
        r = requests.get(next_endpoint, headers=headers, timeout=20)
        r.raise_for_status()
        next_endpoint = process_request(project, r, cutoff_date)
        if not next_endpoint:
            break

def parseSentryTimestamp(t):
    return datetime.datetime.strptime(t[:-1].split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC)

def process_request(project, request, cutoff_date):
    rawDates = [e["dateCreated"] for e in request.json()]
    # throw away "Z" from the end, throw away milliseconds that are sometimes present after "."
    parsedDates = [parseSentryTimestamp(d) for d in rawDates]
    if len(list(filter(lambda d: d > cutoff_date, parsedDates))) == 0:
        return False

    es = list(filter(lambda e: parseSentryTimestamp(e["dateCreated"]) > cutoff_date, request.json()))
    ProjectEndpointCache(project = project, json = json.dumps(es), sample_date = parsedDates[0]).save()

    if "next" in request.links and request.links["next"]["results"] == "true":
        return request.links["next"]["url"]

    return False

@shared_task
def process_project_endpoints(project_id):
    # run all process_endpoint_events in parallel
    # once all are done, run process_stacktraces
    group(
        [
            process_endpoint_events.si(pec['id'])
            for pec in ProjectEndpointCache.objects.filter(project__id=project_id).values('id')
        ]
    )().get(disable_sync_subtasks=False)

@shared_task
def process_endpoint_events(endpoint_cache_id):
    pec = ProjectEndpointCache.objects.get(id=endpoint_cache_id)
    project = pec.project
    events = json.loads(pec.json)
    for e in events:
        # access pattern:
        # read first, if absent try to write; if that fails, another worker could have written
        # already, so try to read which should succeed.
        try:
            group = EventGroup.objects.filter(project=project, group_id = e["groupID"]).first()
            if not group:
                group = EventGroup(project=project, group_id = e["groupID"])
                group.save()
        except IntegrityError:
            group = EventGroup.objects.filter(project=project, group_id = e["groupID"]).first()

        try:
            event = Event.objects.filter(project=project, sentry_id=e["id"]).first()
            if not event:
                event = Event(
                    project=project,
                    group = group,
                    event_id = e["eventID"],
                    sentry_id = e["id"],
                    event_received = e["dateReceived"],
                    event_created = e["dateCreated"],
                    message = e["message"]
                )
                event.save()
        except IntegrityError:
            event = Event.objects.filter(project=project, sentry_id=e["id"]).first()

        for tag in e["tags"]:
            if tag["key"] == "user":
                # too noisy
                continue

            try:
                event_tag = EventTag.objects.filter(project=project, key=tag["key"]).first()
                if not event_tag:
                    event_tag = EventTag(project=project, key=tag["key"])
                    event_tag.save()
            except IntegrityError:
                event_tag = EventTag.objects.filter(project=project, key=tag["key"]).first()

            try:
                keyed = EventTagKeyed.objects.filter(project=project, event_tag=event_tag, value=tag["value"]).first()
                if not keyed:
                    keyed = EventTagKeyed(project=project, event_tag=event_tag, value=tag["value"])
                    keyed.save()
            except IntegrityError:
                keyed = EventTagKeyed.objects.filter(project=project, event_tag=event_tag, value=tag["value"]).first()

            event.tags.add(keyed)

        for entry in e["entries"]:
            if entry["type"] == "exception":
                for val in entry["data"]["values"]:
                    try:
                        frames = val["stacktrace"]["frames"]
                        _, _ = Stacktrace.objects.get_or_create(
                            event=event,
                            stacktrace=format_stacktrace(frames)
                        )
                    except Exception:
                        pass
    pec.delete()

def format_stacktrace(frames):
    return "\n".join([f"{f['module']}#{f['function']}@{f['lineNo']}" for f in reversed(frames)])
