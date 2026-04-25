from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cost/', views.cost_report, name='cost_report'),
    path('performance/', views.performance_report, name='performance_report'),
]