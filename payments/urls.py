from django.urls import path
from . import views
from .mpesa.callbacks import mpesa_callback

urlpatterns = [
    # -------------------------
    # PAYMENTS CORE
    # -------------------------
    path('', views.payment_list, name='payment_list'),
    path('create/', views.payment_form, name='payment_form'),

    # -------------------------
    # ADMIN PAYMENTS
    # -------------------------
    path('admin/', views.admin_payment_list, name='admin_payment_list'),
    path('<int:pk>/verify/', views.verify_payment, name='verify_payment'),

    # -------------------------
    # MPESA CALLBACK (CRITICAL)
    # -------------------------
    path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),
]