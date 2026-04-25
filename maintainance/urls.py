from django.urls import path
from . import views

urlpatterns = [
    path('schedule_list/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),

    path('repairs/', views.repair_logs, name='repair_logs'),
    path('repairs/create/', views.repair_create, name='repair_create'),
]