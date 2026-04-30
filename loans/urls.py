from django.urls import path
from .views import loan_list, create_loan, loan_detail, my_loans

urlpatterns = [
    path('', loan_list, name='loan_list'),
    path('create/', create_loan, name='create_loan'),
    path('<int:pk>/', loan_detail, name='loan_detail'),

    # driver view
    path('my-loans/', my_loans, name='my_loans'),
]