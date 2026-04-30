from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_list, name='schedule_list'),
    path('create/', views.schedule_create, name='schedule_create'),
    path('complete/<int:pk>/', views.mark_complete, name='mark_complete'),

    path('repairs/', views.repair_logs, name='repair_logs'),
    path('repairs/add/', views.add_repair, name='add_repair'),

    path('my/', views.my_maintenance, name='my_maintenance'),
]