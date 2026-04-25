from django.urls import path
from . import views

urlpatterns = [
    path('loan_list/', views.loan_list, name='loan_list'),
    path('loan_create/', views.loan_create, name='loan_create'),
    path('<int:pk>/', views.loan_detail, name='loan_detail'),
]