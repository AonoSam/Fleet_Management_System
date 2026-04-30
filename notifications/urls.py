from django.urls import path
from .views import alerts, unread_count, mark_read, mark_all_read

urlpatterns = [
    path('', alerts, name='alerts'),

    # API endpoints
    path('unread/', unread_count, name='unread_notifications'),
    path('read/<int:pk>/', mark_read, name='mark_read'),
    path('read-all/', mark_all_read, name='mark_all_read'),
]