from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('users/', views.user_list, name='user_list'),
    path('create-user/', views.create_user_view, name='create_user'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('driver-dashboard/', views.driver_dashboard, name='driver_dashboard'),
]