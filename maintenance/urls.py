from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_list, name='schedule_list'),
    path('create/', views.schedule_create, name='schedule_create'),
    path('complete/<int:pk>/', views.mark_complete, name='mark_complete'),

    # Recurring maintenance plans
    path('plans/', views.maintenance_plans, name='maintenance_plans'),
    path('plans/create/', views.maintenance_plan_create, name='maintenance_plan_create'),
    path('plans/<int:pk>/edit/', views.maintenance_plan_edit, name='maintenance_plan_edit'),
    path('plans/<int:pk>/delete/', views.maintenance_plan_delete, name='maintenance_plan_delete'),
    path('plans/<int:pk>/generate-now/', views.maintenance_plan_generate_now, name='maintenance_plan_generate_now'),

    path('repairs/', views.repair_logs, name='repair_logs'),
    path('repairs/add/', views.add_repair, name='add_repair'),
    path('repairs/<int:pk>/', views.repair_detail, name='repair_detail'),
    path('repairs/<int:pk>/edit/', views.edit_repair, name='edit_repair'),
    path('repairs/<int:pk>/delete/', views.delete_repair, name='delete_repair'),

    path('my/', views.my_maintenance, name='my_maintenance'),
]