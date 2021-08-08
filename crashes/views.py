from django.shortcuts import render
from django.core.cache import cache
from .models import Category, CategoryCount, Stacktrace, Event, Project, ComputedTrend

import datetime
from collections import defaultdict

def project(request, project_id):
    project = Project.objects.get(id=project_id)
    stacktraces_all = Stacktrace.objects.filter(event__project=project).count()
    stacktraces_processed = Stacktrace.objects.filter(event__project=project, processed=True).count()

    processed_progress = 0
    latest_event = None
    oldest_event = None
    if stacktraces_all > 0:
        processed_progress = (stacktraces_processed / stacktraces_all) * 100
        latest_event = Event.objects.filter(project=project).order_by('-event_created')[0]
        oldest_event = Event.objects.filter(project=project).order_by('event_created')[0]

    today = datetime.datetime.today()
    cutoff_date = today - datetime.timedelta(days=89)
    date_list = [(today - datetime.timedelta(days=x)).date() for x in range(90)]
    packages = []
    for category in Category.objects.filter(project=project):
        package = {
            "name": category.name,
            "dates": {d.isoformat(): {'info': 0, 'fatal': 0} for d in date_list},
            "trends": {d: {'info': 0, 'fatal': 0} for d in range(len(date_list))}
        }
        for cc in CategoryCount.objects.filter(category=category, date__gte=cutoff_date):
            package['dates'][cc.date.isoformat()]['info'] = cc.info_count
            package['dates'][cc.date.isoformat()]['fatal'] = cc.fatal_count

        for ct in ComputedTrend.objects.filter(category=category, for_date=today, days_back__lt=len(date_list)):
            package['trends'][ct.days_back]['info'] = ct.info_trend
            package['trends'][ct.days_back]['fatal'] = ct.fatal_trend

        packages.append(package)

    # for p in Category.objects.filter(project=project):
    #     package = cache.get('p_%s_computed_package_category_id_%s' % (project.id, p.id))
    #     if package:
    #         packages.append(package)

    return render(request, 'crashes/packages.html', {
        'project': project,
        'packages': packages,
        'stacktraces_processed': stacktraces_processed,
        'stacktraces_all': stacktraces_all,
        'processed_progress': processed_progress,
        'latest_event': latest_event,
        'oldest_event': oldest_event
    })

def package(request, project_id, package_name):
    today = datetime.datetime.today()
    cutoff_date = today - datetime.timedelta(days=29)
    date_list = [(today - datetime.timedelta(days=x)).date() for x in range(30)]
    p = Category.objects.get(project__id=project_id, name=package_name)
    package = {
        "name": p.name,
        "groups": []
    }
    for group in p.eventgroup_set.all():
        g = {
            "id": group.id,
            "event_count": group.event_count(),
            "url": "https://sentry.prod.mozaws.net/operations/firefox-nightly/issues/%s" % group.group_id,
            "events": [],
            "dates": {d.isoformat(): {'info': 0, 'fatal': 0} for d in date_list}
        }
        for event in group.event_set.filter(event_created__gte=cutoff_date):
            s = event.stacktrace_set.all().first()
            if s:
                s = s.stacktrace
            else:
                s = ""
            g['events'].append({
                "id": event.id,
                "is_info": event.is_info(),
                "url": "https://sentry.prod.mozaws.net/operations/firefox-nightly/issues/%s/events/%s/" % (event.group.group_id, event.sentry_id),
                "message": event.message,
                "stacktrace": s
            })
            if event.is_info():
                g['dates'][event.event_created.date().isoformat()]['info'] += 1
            else:
                g['dates'][event.event_created.date().isoformat()]['fatal'] += 1

        package['groups'].append(g)

    return render(request, 'crashes/package.html', {
        'project': p.project,
        'package': package
    })
