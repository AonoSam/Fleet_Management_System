from django.shortcuts import render, redirect
from accounts.permissions import admin_required, driver_required
from .services import get_all_loans, get_driver_loans, get_loan, update_loan_status
from accounts.models import User
from .models import Loan


# -----------------------
# ADMIN: LOAN LIST
# -----------------------
@admin_required
def loan_list(request):
    loans = get_all_loans()
    return render(request, 'loan_list.html', {'loans': loans})


# -----------------------
# ADMIN: CREATE LOAN
# -----------------------
@admin_required
def create_loan(request):
    drivers = User.objects.filter(role='DRIVER')

    if request.method == 'POST':
        Loan.objects.create(
            driver_id=request.POST.get('driver'),
            amount=request.POST.get('amount'),
            purpose=request.POST.get('purpose'),
            interest_rate=request.POST.get('interest_rate'),
            due_date=request.POST.get('due_date'),
            status='ACTIVE'
        )
        return redirect('loan_list')

    return render(request, 'loan_form.html', {'drivers': drivers})


# -----------------------
# ADMIN: LOAN DETAIL
# -----------------------
@admin_required
def loan_detail(request, pk):
    loan = get_loan(pk)
    return render(request, 'loan_detail.html', {'loan': loan})


# -----------------------
# DRIVER: MY LOANS
# -----------------------
@driver_required
def my_loans(request):
    loans = get_driver_loans(request.user)
    return render(request, 'loan_list.html', {'loans': loans})