from django.shortcuts import render
from .models import Category

# Create your views here.
def packages(request):
    packages = Category.objects.all()
    return render(request, 'crashes/packages.html', {
        'packages': packages
    })

def package(request, package_name):
    package = Category.objects.get(name=package_name)
    return render(request, 'crashes/package.html', {
        'package': package
    })
