from django.urls import path
from . import views

urlpatterns = [
    path('',              views.alerts,               name='alerts'),
    path('unread/',       views.unread_count,          name='unread_notifications'),
    path('read/<int:pk>/',        views.mark_read,     name='mark_read'),
    path('read-all/',             views.mark_all_read, name='mark_all_read'),
    path('delete/<int:pk>/',      views.delete_notification, name='delete_notification'),
    path('delete-selected/',      views.delete_selected,     name='delete_selected'),
    path('delete-all/',           views.delete_all,          name='delete_all'),
]