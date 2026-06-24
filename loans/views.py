from decimal import Decimal, ROUND_HALF_UP
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
@login_required
def loan_detail(request, pk):

    loan = get_loan(pk)

    if request.user.role == 'DRIVER' and loan.driver != request.user:
        messages.error(request, "You are not allowed to view this loan.")
        return redirect('my_loans')

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

    if loan.loan_type == 'DRIVER' and loan.interest_rate == 0:
        loan.interest_rate = calculate_driver_interest(loan.amount)

    loan.status = 'ACTIVE'
    loan.approved_by = request.user
    loan.save()

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
# REPAY LOAN (MPESA + MANUAL)
#
# ✅ FIXED:
# 1. M-Pesa amounts are rounded to the nearest whole shilling
#    before being sent to Safaricom (M-Pesa rejects decimals
#    and amounts below KSh 1). The rounding is shown to the
#    user BEFORE submission so there are no surprises.
# 2. Overpayment is now explicitly allowed. If the entered
#    amount exceeds the remaining balance, the system still
#    accepts it, records the FULL amount paid, marks the loan
#    PAID, and informs the user of the excess so it's visible
#    rather than silently absorbed.
# 3. Bank loans remain manual/cash only.
# -----------------------
@login_required
def repay_loan(request, pk):

    loan = get_loan(pk)

    if request.user.role == 'DRIVER' and loan.driver != request.user:
        messages.error(request, "Not allowed.")
        return redirect('my_loans')

    if request.method == 'POST':

        try:
            amount = Decimal(request.POST.get('amount') or 0)
        except Exception:
            messages.error(request, "Invalid amount.")
            return redirect('loan_detail', pk=pk)

        method = request.POST.get('method')
        phone_number = request.POST.get('phone_number')

        if amount <= 0:
            messages.error(request, "Invalid amount.")
            return redirect('loan_detail', pk=pk)

        # Block M-Pesa for BANK loans
        if loan.loan_type == 'BANK' and method == 'MPESA':
            messages.error(
                request,
                "Bank loans can only be repaid manually/cash for now. "
                "Direct bank integration (KCB/Equity) is coming soon."
            )
            return redirect('loan_detail', pk=pk)

        # Detect overpayment up front so we can inform the user either way
        balance_before = loan.balance()
        is_overpayment = amount > balance_before

        # =========================
        # MPESA FLOW (driver loans only)
        # =========================
        if method == "MPESA":

            if not phone_number or not phone_number.startswith("07"):
                messages.error(request, "Enter valid phone number.")
                return redirect('loan_detail', pk=pk)

            # ── Round to the nearest whole shilling for M-Pesa ──
            # M-Pesa STK Push rejects decimal amounts and anything
            # below KSh 1. We round HALF_UP (4000.40 -> 4000,
            # 4000.50 -> 4001) and tell the user what will actually
            # be charged.
            mpesa_amount = amount.to_integral_value(rounding=ROUND_HALF_UP)

            if mpesa_amount < 1:
                messages.error(request, "Amount must be at least KSh 1 for M-Pesa.")
                return redirect('loan_detail', pk=pk)

            from payments.services import create_payment
            from payments.mpesa.client import MpesaClient
            from django.conf import settings

            payment = create_payment({
                "driver": loan.driver,
                "loan": loan,
                "payment_type": "LOAN_REPAYMENT",
                "amount": mpesa_amount,
                "phone_number": phone_number,
                "status": "PENDING"
            })

            mpesa = MpesaClient()

            response = mpesa.stk_push(
                phone_number="254" + phone_number[1:],
                amount=mpesa_amount,
                reference=payment.reference,
                callback_url=settings.MPESA_CALLBACK_URL
            )

            if not response.get("success"):
                payment.delete()
                messages.error(request, f"STK failed: {response.get('message')}")
                return redirect('loan_detail', pk=pk)

            checkout_id = response.get("checkout_request_id")
            if checkout_id:
                payment.reference = checkout_id
                payment.save(update_fields=['reference'])

            if mpesa_amount != amount:
                messages.info(
                    request,
                    f"M-Pesa requires whole shillings — KSh {amount} was rounded to KSh {mpesa_amount}."
                )

            messages.success(request, "STK sent. Complete payment on your phone.")
            return redirect('loan_detail', pk=pk)

        # =========================
        # MANUAL FLOW (driver + bank loans)
        # No rounding needed — cash/manual entries can carry
        # cents exactly as entered.
        # =========================
        else:
            record_repayment(loan, amount)

            if loan.driver:
                create_notification(
                    loan.driver,
                    f"Manual repayment of KSh {amount} recorded.",
                    'PAYMENT'
                )

            if is_overpayment:
                excess = amount - balance_before
                messages.success(
                    request,
                    f"Repayment of KSh {amount} recorded. This loan is now fully paid, "
                    f"with an excess of KSh {excess} over the remaining balance."
                )
            else:
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