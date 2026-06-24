from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal, InvalidOperation

from django.urls import reverse

from accounts.permissions import driver_required, admin_required
from vehicles.models import Vehicle
from .models import Payment
from django.conf import settings
from .services import (
    create_payment,
    get_driver_payments,
    get_all_payments,
    update_payment_status
)

from .mpesa.client import MpesaClient

# -------------------------
# DRIVER: CREATE PAYMENT (FIXED MPESA FLOW)
# -------------------------
@driver_required
def payment_form(request):
    vehicle = Vehicle.objects.filter(assigned_driver=request.user).first()

    if not vehicle:
        messages.error(request, "You are not assigned to any vehicle.")
        return redirect('payment_list')

    if request.method == 'POST':
        amount       = request.POST.get('amount')
        phone_number = request.POST.get('phone_number')

        if not amount or not phone_number:
            messages.error(request, "All fields required.")
            return redirect('payment_form')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Invalid amount.")
            return redirect('payment_form')

        if not phone_number.startswith("07") or len(phone_number) != 10:
            messages.error(request, "Invalid phone number. Use format 07XXXXXXXX.")
            return redirect('payment_form')

        # ── Step 1: Create payment record ──
        payment = Payment.objects.create(
            driver=request.user,
            vehicle=vehicle,
            amount=amount,
            phone_number=phone_number,
            status="PENDING"
        )

        # ── Step 2: Fire STK push ──
        from django.conf import settings
        mpesa = MpesaClient()

        response = mpesa.stk_push(
            phone_number=phone_number,
            amount=amount,
            reference=payment.reference,
            callback_url=settings.MPESA_CALLBACK_URL
        )

        if not response.get("success"):
            payment.delete()
            messages.error(request, f"M-Pesa error: {response.get('message')}")
            return redirect('payment_form')

        # ── Step 3: Save checkout ID as reference ──
        checkout_id = response.get("checkout_request_id")
        if checkout_id:
            payment.reference = checkout_id
            payment.save(update_fields=['reference'])

        messages.success(request, "STK Push sent. Enter your M-Pesa PIN.")
        return redirect('payment_list')

    return render(request, 'payment_form.html', {'vehicle': vehicle})


# -------------------------
# DRIVER PAYMENTS
# -------------------------
@driver_required
def payment_list(request):
    return render(request, 'payment_list.html', {
        'payments': get_driver_payments(request.user)
    })


# -------------------------
# ADMIN PAYMENTS
# -------------------------
@admin_required
def admin_payment_list(request):
    return render(request, 'payment_list.html', {
        'payments': get_all_payments()
    })


# -------------------------
# MANUAL VERIFY (FALLBACK ONLY)
# -------------------------

@admin_required
def verify_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if payment.status == 'SUCCESS':
        messages.info(request, "This payment is already marked as successful.")
    elif payment.status == 'FAILED':
        messages.warning(request, "This payment failed and cannot be verified.")
    else:
        # Manual fallback: admin confirms a PENDING payment as
        # successful (e.g. M-Pesa callback didn't arrive but the
        # admin confirmed receipt via M-Pesa statement/SMS).
        # The post_save signal will automatically fire the
        # admin notification once status flips to SUCCESS.
        payment.status = 'SUCCESS'
        payment.save(update_fields=['status'])
        messages.success(request, "Payment manually verified and marked as successful.")

    return redirect('admin_payment_list')