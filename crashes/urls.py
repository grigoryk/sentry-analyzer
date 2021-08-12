from django.urls import path
from . import views

urlpatterns = [
    path('<slug:org_slug>/', views.org, name='org'),
    path('<slug:org_slug>/<slug:project_slug>/', views.project, name='project'),
    path('<slug:org_slug>/<slug:project_slug>/package/<str:package_name>/', views.package, name='package')
]
