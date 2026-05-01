from django.urls import path
from .views import (
    loan_list,
    create_loan,
    request_loan,  # ✅ NEW
    loan_detail,
    my_loans,
    approve_loan,
    reject_loan,
    repay_loan
)

urlpatterns = [
    path('', loan_list, name='loan_list'),

    # ADMIN
    path('create/', create_loan, name='create_loan'),

    # DRIVER
    path('request/', request_loan, name='request_loan'),  # ✅ NEW

    path('<int:pk>/', loan_detail, name='loan_detail'),

    path('<int:pk>/approve/', approve_loan, name='approve_loan'),
    path('<int:pk>/reject/', reject_loan, name='reject_loan'),
    path('<int:pk>/repay/', repay_loan, name='repay_loan'),

    path('my-loans/', my_loans, name='my_loans'),
]