from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('modules/<slug:entity>/', views.entity_list, name='entity_list'),
    path('modules/<slug:entity>/new/', views.entity_create, name='entity_create'),
    path('modules/<slug:entity>/<int:pk>/edit/', views.entity_update, name='entity_update'),
    path('api/', include(views.router.urls)),
]
