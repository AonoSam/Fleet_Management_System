from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.permissions import admin_required, driver_required
from accounts.models import User

from .models import Loan
from .services import (
    get_all_loans,
    get_driver_loans,
    get_loan,
    record_repayment,
    calculate_total_amount,
    calculate_driver_interest
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
            requested_by=request.user
        )

        # Notifications
        if loan.loan_type == 'DRIVER' and loan.driver:
            create_notification(
                loan.driver,
                f"You have been issued a loan of KSh {loan.amount}. Awaiting approval.",
                'SYSTEM'
            )

        elif loan.loan_type == 'BANK':
            create_notification(
                request.user,
                f"Company loan of KSh {loan.amount} recorded.",
                'SYSTEM'
            )

        messages.success(request, "Loan created successfully.")
        return redirect('loan_list')

    return render(request, 'loan_form.html', {
        'drivers': drivers
    })


# -----------------------
# DRIVER REQUEST LOAN
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
            interest_rate=Decimal('0.00'),
            due_date=request.POST.get('due_date') or None,
            status='REQUESTED',
            requested_by=request.user
        )

        # Notify admins
        admins = User.objects.filter(role='ADMIN')

        for admin in admins:
            create_notification(
                admin,
                f"{request.user.username} requested a loan of KSh {loan.amount}.",
                'SYSTEM'
            )

        messages.success(request, "Loan request submitted.")
        return redirect('my_loans')

    return render(request, 'loan_form.html')


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
# APPROVE LOAN (FIXED FLOW)
# -----------------------
@admin_required
def approve_loan(request, pk):

    loan = get_loan(pk)

    # 🔥 apply interest ONLY once
    if loan.loan_type == 'DRIVER' and loan.interest_rate == 0:
        loan.interest_rate = calculate_driver_interest(loan.amount)

    loan.status = 'ACTIVE'
    loan.approved_by = request.user
    loan.save()

    # Notify driver
    if loan.driver:
        create_notification(
            loan.driver,
            f"Loan of KSh {loan.amount} approved at {loan.interest_rate}%.",
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
# REPAY LOAN (MPESA + MANUAL FIXED)
# -----------------------
@login_required
def repay_loan(request, pk):

    loan = get_loan(pk)

    # 🔐 SECURITY
    if request.user.role == 'DRIVER' and loan.driver != request.user:
        messages.error(request, "Not allowed.")
        return redirect('my_loans')

    if request.method == 'POST':

        amount = Decimal(request.POST.get('amount') or 0)
        method = request.POST.get('method')
        phone_number = request.POST.get('phone_number')

        if amount <= 0:
            messages.error(request, "Invalid amount.")
            return redirect('loan_detail', pk=pk)

        # =========================
        # 🔵 MPESA FLOW
        # =========================
        if method == "MPESA":

            if not phone_number or not phone_number.startswith("07"):
                messages.error(request, "Enter valid phone number.")
                return redirect('loan_detail', pk=pk)

            from payments.services import create_payment
            from payments.mpesa.client import MpesaClient
            from django.urls import reverse

            # 🔥 CREATE PAYMENT (LINKED TO LOAN)
            payment = create_payment({
                "driver": loan.driver,
                "loan": loan,
                "payment_type": "LOAN_REPAYMENT",
                "amount": amount,
                "phone_number": phone_number,
                "status": "PENDING"
            })

            # 🔥 INITIATE STK
            mpesa = MpesaClient()

            callback_url = request.build_absolute_uri(
                reverse('mpesa_callback')
            )

            response = mpesa.stk_push(
                phone_number="254" + phone_number[1:],
                amount=amount,
                reference=payment.reference,
                callback_url=callback_url
            )

            # 🔥 HANDLE FAILURE (CRITICAL)
            if not response.get("success"):
                payment.delete()

                messages.error(request, f"STK failed: {response.get('message')}")
                return redirect('loan_detail', pk=pk)

            # 🔥 SAVE CHECKOUT ID
            checkout_id = response.get("checkout_request_id")

            if checkout_id:
                payment.reference = checkout_id
                payment.save(update_fields=['reference'])

            messages.success(request, "STK sent. Complete payment on your phone.")
            return redirect('loan_detail', pk=pk)

        # =========================
        # 🟡 MANUAL FLOW
        # =========================
        else:

            record_repayment(loan, amount)

            if loan.driver:
                create_notification(
                    loan.driver,
                    f"Manual repayment of KSh {amount} recorded.",
                    'PAYMENT'
                )

            messages.success(request, "Manual repayment recorded.")
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