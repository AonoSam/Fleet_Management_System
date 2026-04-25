from django.urls import path
from .views import alerts_view

urlpatterns = [
    path('alerts/', alerts_view, name='alerts'),
]