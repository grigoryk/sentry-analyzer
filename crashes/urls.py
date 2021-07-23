from django.urls import include, path
from . import views

urlpatterns = [
    path('<int:project_id>', views.project, name='project'),
    path('<int:project_id>/package/<str:package_name>', views.package, name='package')
]
