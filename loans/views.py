from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.permissions import admin_required, driver_required
from accounts.models import User

from .models import Loan
from .services import (
    get_all_loans,
    get_driver_loans,
    get_loan,
    record_repayment,
    calculate_total_amount
)

from notifications.services import create_notification


# -----------------------
# LOAN LIST (ADMIN)
# -----------------------
@admin_required
def loan_list(request):

    loan_type = request.GET.get('type')
    status = request.GET.get('status')

    loans = get_all_loans(loan_type, status)

    return render(request, 'loan_list.html', {
        'loans': loans
    })


# -----------------------
# CREATE LOAN (ADMIN ISSUE)
# -----------------------
@admin_required
def create_loan(request):

    drivers = User.objects.filter(role='DRIVER')

    if request.method == 'POST':

        loan_type = request.POST.get('loan_type')

        amount = Decimal(request.POST.get('amount') or 0)
        interest_rate = Decimal(request.POST.get('interest_rate') or 0)

        loan = Loan.objects.create(
            loan_type=loan_type,
            driver_id=request.POST.get('driver') if loan_type == 'DRIVER' else None,
            amount=amount,
            purpose=request.POST.get('purpose'),
            interest_rate=interest_rate,
            due_date=request.POST.get('due_date') or None,
            status='PENDING',
            requested_by=request.user  # ✅ admin initiated
        )

        # 🔔 NOTIFICATIONS
        if loan.loan_type == 'DRIVER' and loan.driver:
            create_notification(
                loan.driver,
                f"You have been issued a loan of KSh {loan.amount}. Waiting for approval.",
                'SYSTEM'
            )

        elif loan.loan_type == 'BANK':
            create_notification(
                request.user,
                f"Company bank loan of KSh {loan.amount} recorded.",
                'SYSTEM'
            )

        messages.success(request, "Loan created successfully.")
        return redirect('loan_list')

    return render(request, 'loan_form.html', {
        'drivers': drivers
    })


# -----------------------
# DRIVER REQUEST LOAN ✅ NEW
# -----------------------
@driver_required
def request_loan(request):

    if request.method == 'POST':

        amount = Decimal(request.POST.get('amount') or 0)

        loan = Loan.objects.create(
            loan_type='DRIVER',
            driver=request.user,
            amount=amount,
            purpose=request.POST.get('purpose'),
            interest_rate=Decimal('0.00'),  # admin sets later if needed
            due_date=request.POST.get('due_date') or None,
            status='PENDING',
            requested_by=request.user  # ✅ driver initiated
        )

        # 🔔 Notify admin(s)
        admins = User.objects.filter(role='ADMIN')

        for admin in admins:
            create_notification(
                admin,
                f"{request.user.username} requested a loan of KSh {loan.amount}.",
                'SYSTEM'
            )

        messages.success(request, "Loan request submitted. Awaiting approval.")
        return redirect('my_loans')

    return render(request, 'loan_form.html')  # reuse same form


# -----------------------
# LOAN DETAIL
# -----------------------
@admin_required
def loan_detail(request, pk):

    loan = get_loan(pk)

    return render(request, 'loan_detail.html', {
        'loan': loan,
        'total_amount': calculate_total_amount(loan)
    })


# -----------------------
# APPROVE LOAN
# -----------------------
@admin_required
def approve_loan(request, pk):

    loan = get_loan(pk)

    loan.status = 'ACTIVE'
    loan.approved_by = request.user
    loan.save()

    if loan.driver:
        create_notification(
            loan.driver,
            f"Your loan of KSh {loan.amount} has been APPROVED.",
            'SYSTEM'
        )

    messages.success(request, "Loan approved.")
    return redirect('loan_list')


# -----------------------
# REJECT LOAN
# -----------------------
@admin_required
def reject_loan(request, pk):

    loan = get_loan(pk)

    loan.status = 'REJECTED'
    loan.approved_by = request.user
    loan.save()

    if loan.driver:
        create_notification(
            loan.driver,
            "Your loan request was rejected.",
            'SYSTEM'
        )

    messages.warning(request, "Loan rejected.")
    return redirect('loan_list')


# -----------------------
# REPAY LOAN
# -----------------------
@admin_required
def repay_loan(request, pk):

    loan = get_loan(pk)

    if request.method == 'POST':

        amount = Decimal(request.POST.get('amount') or 0)

        record_repayment(loan, amount)

        if loan.driver:
            create_notification(
                loan.driver,
                f"Repayment of KSh {amount} recorded.",
                'PAYMENT'
            )

        messages.success(request, "Repayment recorded.")
        return redirect('loan_detail', pk=pk)

    return render(request, 'loan_repay.html', {
        'loan': loan
    })


# -----------------------
# DRIVER LOANS
# -----------------------
@driver_required
def my_loans(request):

    loans = get_driver_loans(request.user)

    return render(request, 'loan_list.html', {
        'loans': loans
    })