from django.shortcuts import render
from django.views.decorators.cache import cache_page
from .models import Category

import datetime
from collections import defaultdict

@cache_page(60 * 30)
def packages(request):
    packages = []
    today = datetime.datetime.today()
    cutoff_date = today - datetime.timedelta(days=29)
    date_list = [(today - datetime.timedelta(days=x)).date() for x in range(30)]

    for p in Category.objects.all():
        package = {
            "name": p.name,
            "dates": {d.isoformat(): {'info': 0, 'fatal': 0} for d in date_list}
        }
        for group in p.eventgroup_set.all():
            for event in group.event_set.filter(event_created__gte=cutoff_date):
                if event.is_info():
                    package['dates'][event.event_created.date().isoformat()]['info'] += 1
                else:
                    package['dates'][event.event_created.date().isoformat()]['fatal'] += 1
        packages.append(package)
    return render(request, 'crashes/packages.html', {
        'packages': packages
    })

def package(request, package_name):
    package = Category.objects.get(name=package_name)
    return render(request, 'crashes/package.html', {
        'package': package
    })
