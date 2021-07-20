from django.urls import include, path
from . import views

urlpatterns = [
    path('packages/', views.packages, name='packages'),
    path('package/<str:package_name>', views.package, name='package')
]
