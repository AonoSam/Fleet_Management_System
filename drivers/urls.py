from django.urls import path
from . import views

urlpatterns = [
    path('', views.driver_list, name='driver_list'),
    path('create/', views.driver_create, name='driver_create'),
    path('<int:pk>/edit/', views.driver_update, name='driver_update'),
    path('<int:pk>/performance/', views.driver_performance, name='driver_performance'),
    path('my-vehicle/', views.my_vehicle, name='my_vehicle'),
    path('delete/<int:pk>/', views.driver_delete, name='driver_delete'),
]