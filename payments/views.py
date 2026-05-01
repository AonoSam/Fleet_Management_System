from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal, InvalidOperation

from django.urls import reverse

from accounts.permissions import driver_required, admin_required
from vehicles.models import Vehicle
from .models import Payment
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

        amount = request.POST.get('amount')
        phone_number = request.POST.get('phone_number')

        # -------------------------
        # VALIDATION
        # -------------------------
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
            messages.error(request, "Invalid phone number.")
            return redirect('payment_form')

        # -------------------------
        # CREATE PAYMENT (TEMP)
        # -------------------------
        payment = create_payment({
            "driver": request.user,
            "vehicle": vehicle,
            "amount": amount,
            "phone_number": phone_number,
            "status": "PENDING"
        })

        # -------------------------
        # INITIATE STK PUSH
        # -------------------------
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

        # -------------------------
        # HANDLE STK RESPONSE (CRITICAL FIX)
        # -------------------------
        if not response.get("success"):
            # ❌ STK FAILED → DELETE PAYMENT
            payment.delete()

            messages.error(request, f"Payment failed: {response.get('message')}")
            return redirect('payment_form')

        # -------------------------
        # STK SUCCESS → SAVE CHECKOUT ID
        # -------------------------
        checkout_id = response.get("checkout_request_id")

        if checkout_id:
            payment.reference = checkout_id
            payment.save(update_fields=['reference'])

        messages.success(request, "STK Push sent. Enter PIN on your phone.")
        return redirect('payment_list')

    return render(request, 'payment_form.html', {
        'vehicle': vehicle
    })


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

    if payment.status != 'SUCCESS':
        messages.warning(request, "Only completed MPESA payments can be verified.")
    return redirect('admin_payment_list')