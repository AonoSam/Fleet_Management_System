from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.permissions import admin_required, driver_required
from accounts.models import User, DriverProfile

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

# ── FIX: import the shared phone validation utility ──
# This is the single source of truth for Kenyan phone validation
# (handles 07XXXXXXXX, 01XXXXXXXX, 254XXXXXXXXX, +254XXXXXXXXX).
# Previously this file had its own startswith("07") check that
# rejected valid 01-prefixed Safaricom numbers.
from payments.phone_utils import normalize_phone, InvalidPhoneNumberError


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

    available_credit = Decimal('0.00')
    if loan.driver:
        profile, _ = DriverProfile.objects.get_or_create(user=loan.driver)
        available_credit = profile.credit_balance

    return render(request, 'loan_detail.html', {
        'loan': loan,
        'total_amount': calculate_total_amount(loan),
        'available_credit': available_credit,
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
# APPLY DRIVER CREDIT TO THIS LOAN
# (Admin-triggered only, as decided)
# -----------------------
@admin_required
def apply_credit(request, pk):

    loan = get_loan(pk)

    if request.method != 'POST':
        return redirect('loan_detail', pk=pk)

    if not loan.driver:
        messages.error(request, "Credit can only be applied to driver loans.")
        return redirect('loan_detail', pk=pk)

    if loan.status != 'ACTIVE':
        messages.error(request, "Credit can only be applied to active loans.")
        return redirect('loan_detail', pk=pk)

    profile, _ = DriverProfile.objects.get_or_create(user=loan.driver)

    if profile.credit_balance <= 0:
        messages.warning(request, f"{loan.driver.username} has no available credit.")
        return redirect('loan_detail', pk=pk)

    balance_due = loan.balance()

    if balance_due <= 0:
        messages.info(request, "This loan is already fully paid.")
        return redirect('loan_detail', pk=pk)

    amount_to_apply = min(profile.credit_balance, balance_due)

    record_repayment(loan, amount_to_apply, source='CREDIT')

    profile.credit_balance -= amount_to_apply
    profile.save(update_fields=['credit_balance'])

    create_notification(
        loan.driver,
        f"KSh {amount_to_apply} of your credit balance was applied to this loan.",
        'PAYMENT'
    )

    messages.success(
        request,
        f"KSh {amount_to_apply} applied from {loan.driver.username}'s credit balance. "
        f"Remaining credit: KSh {profile.credit_balance}."
    )
    return redirect('loan_detail', pk=pk)


# -----------------------
# REPAY LOAN (MPESA + MANUAL)
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

        if loan.loan_type == 'BANK' and method == 'MPESA':
            messages.error(
                request,
                "Bank loans can only be repaid manually/cash for now. "
                "Direct bank integration (KCB/Equity) is coming soon."
            )
            return redirect('loan_detail', pk=pk)

        balance_before = loan.balance()
        is_overpayment = amount > balance_before

        # =========================
        # MPESA FLOW (driver loans only)
        # =========================
        if method == "MPESA":

            # ── FIX: validate + normalize via the shared utility
            #    instead of the old startswith("07") check ──
            try:
                normalized_phone = normalize_phone(phone_number)
            except InvalidPhoneNumberError as e:
                messages.error(request, str(e))
                return redirect('loan_detail', pk=pk)

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
                "phone_number": normalized_phone,
                "status": "PENDING"
            })

            mpesa = MpesaClient()

            # ── FIX: pass the already-normalized number directly.
            #    The old code did "254" + phone_number[1:], which
            #    assumed the number always started with a single
            #    leading 0 — MpesaClient.stk_push() now normalizes
            #    internally too, so this is also defensively safe
            #    even if passed a local-format number by mistake. ──
            response = mpesa.stk_push(
                phone_number=normalized_phone,
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

            # Overpayment crediting for M-Pesa happens in the
            # M-Pesa callback once payment is confirmed SUCCESS
            # (see payments/mpesa/callbacks.py), since the
            # repayment isn't recorded until then.

            messages.success(request, "STK sent. Complete payment on your phone.")
            return redirect('loan_detail', pk=pk)

        # =========================
        # MANUAL FLOW (driver + bank loans)
        # =========================
        else:
            _apply_repayment_with_credit_tracking(loan, amount, balance_before, is_overpayment)

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
                    f"Repayment of KSh {amount} recorded. This loan is now fully paid. "
                    f"The excess of KSh {excess} has been added to "
                    f"{loan.driver.username if loan.driver else 'the company'}'s credit balance "
                    f"for use on a future loan."
                )
            else:
                messages.success(request, "Manual repayment recorded.")

            return redirect('loan_detail', pk=pk)

    return render(request, 'loan_repay.html', {
        'loan': loan
    })


def _apply_repayment_with_credit_tracking(loan, amount, balance_before, is_overpayment):
    """
    Records the repayment on the loan. If the amount exceeds the
    remaining balance, only the balance portion goes against the
    loan and the excess is banked as credit on the driver's
    DriverProfile (Bank/company loans have no driver, so credit
    only applies to driver loans).
    """
    if is_overpayment and loan.driver:
        excess = amount - balance_before
        amount_applied_to_loan = balance_before

        if amount_applied_to_loan > 0:
            record_repayment(loan, amount_applied_to_loan)

        profile, _ = DriverProfile.objects.get_or_create(user=loan.driver)
        profile.credit_balance += excess
        profile.save(update_fields=['credit_balance'])

    else:
        record_repayment(loan, amount)


# -----------------------
# DRIVER LOANS
# -----------------------
@driver_required
def my_loans(request):

    loans = get_driver_loans(request.user)

    profile, _ = DriverProfile.objects.get_or_create(user=request.user)

    return render(request, 'loan_list.html', {
        'loans': loans,
        'available_credit': profile.credit_balance,
    })