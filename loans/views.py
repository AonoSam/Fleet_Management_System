from django.shortcuts import render, redirect, get_object_or_404
from drivers.models import Driver
from .models import Loan
from .services import get_loans, create_loan, get_loan, add_repayment


# =====================
# LOAN LIST
# =====================
def loan_list(request):
    loans = get_loans()

    return render(request, 'loan_list.html', {
        'loans': loans
    })


# =====================
# CREATE LOAN
# =====================
def loan_create(request):

    drivers = Driver.objects.all()

    if request.method == "POST":

        driver = get_object_or_404(Driver, id=request.POST.get('driver'))

        data = {
            "driver": driver,
            "amount": request.POST.get('amount'),
            "reason": request.POST.get('reason')
        }

        create_loan(data)
        return redirect('loan_list')

    # ✅ FIX: MUST LOAD A FORM TEMPLATE, NOT loan_list.html
    return render(request, 'loan_form.html', {
        'drivers': drivers
    })


# =====================
# LOAN DETAIL + REPAYMENT
# =====================
def loan_detail(request, pk):

    loan = get_loan(pk)

    if request.method == "POST":

        amount = request.POST.get('amount_paid')
        add_repayment(loan, amount)

        return redirect('loan_detail', pk=pk)

    return render(request, 'loan_detail.html', {
        'loan': loan
    })