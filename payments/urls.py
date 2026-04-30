from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('create/', views.payment_form, name='payment_form'),
    path('admin/', views.admin_payment_list, name='admin_payment_list'),

    # 🔥 NEW VERIFY ROUTE
    path('<int:pk>/verify/', views.verify_payment, name='verify_payment'),
]