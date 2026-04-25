from django.urls import path
from . import views

urlpatterns = [
    path('payment_list/', views.payment_list, name='payment_list'),
    path('create/', views.payment_create, name='payment_create'),
    path('mpesa-status/', views.mpesa_status, name='mpesa_status'),
]