from django.urls import path
from . import views

urlpatterns = [
    path('driver_list/', views.driver_list, name='driver_list'),
    path('create/', views.driver_create, name='driver_create'),
    path('performance/<int:pk>/', views.performance_view, name='driver_performance'),
]