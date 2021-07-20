from django.shortcuts import render
from .models import Category

# Create your views here.
def packages(request):
    packages = Category.objects.all()
    return render(request, 'crashes/packages.html', {
        'packages': packages
    })
