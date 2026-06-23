from django.urls import path
from . import views

urlpatterns = [
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),

    # User management
    path('users/',                views.user_list,       name='user_list'),
    path('create-user/',          views.create_user_view, name='create_user'),
    path('edit-user/<int:pk>/',   views.edit_user,       name='edit_user'),
    path('delete-user/<int:pk>/', views.delete_user,     name='delete_user'),

    # Dashboards
    path('admin-dashboard/',  views.admin_dashboard,  name='admin_dashboard'),
    path('driver-dashboard/', views.driver_dashboard, name='driver_dashboard'),

    # Session management
    path('active-users/',              views.active_users,      name='active_users'),
    path('force-logout/<int:pk>/',     views.force_logout_user, name='force_logout_user'),
    path('block-user/<int:pk>/',       views.block_user,        name='block_user'),
    path('unblock-user/<int:pk>/',     views.unblock_user,      name='unblock_user'),
]