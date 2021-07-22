from django.shortcuts import render
from django.core.cache import cache
from .models import Category, Stacktrace

import datetime
from collections import defaultdict

def packages(request):
    packages = []
    stacktraces_all = Stacktrace.objects.all().count()
    stacktraces_processed = Stacktrace.objects.filter(processed=True).count()
    stacktraces_not_processed = Stacktrace.objects.filter(processed=False).count()
    processed_progress = (stacktraces_processed / stacktraces_all) * 100

    for p in Category.objects.all():
        package = cache.get('computed_package_category_id_%s' % p.id)
        if package:
            packages.append(package)

    return render(request, 'crashes/packages.html', {
        'packages': packages,
        'stacktraces_processed': stacktraces_processed,
        'stacktraces_all': stacktraces_all,
        'processed_progress': processed_progress
    })

def package(request, package_name):
# {% for group in package.package.eventgroup_set.all %}
#             { id: '{{ group.group_id }}', event_count: {{ group.event_count }}, url: 'https://sentry.prod.mozaws.net/operations/firefox-nightly/issues/{{ group.group_id }}', events:
#                 [
#                 {% for event in group.event_set.all %}
#                     { id: '{{ event.id }}', is_info: {{ event.is_info|yesno:"true,false" }}, url: 'https://sentry.prod.mozaws.net/operations/firefox-nightly/issues/{{ group.group_id }}/events/{{ event.sentry_id }}/', message: '{{ event.message|escapejs }}', stacktrace: '{{ event.stacktrace_set.all.0.stacktrace|escapejs }}'},
#                 {% endfor %}
#                 ]
#             },
#             {% endfor %}

    today = datetime.datetime.today()
    cutoff_date = today - datetime.timedelta(days=29)
    date_list = [(today - datetime.timedelta(days=x)).date() for x in range(30)]
    p = Category.objects.get(name=package_name)
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
        'package': package
    })
