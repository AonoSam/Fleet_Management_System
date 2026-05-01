from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from decimal import Decimal, InvalidOperation


from accounts.permissions import driver_required, admin_required
from vehicles.models import Vehicle
from .models import Payment
from .services import (
    create_payment,
    get_driver_payments,
    get_all_payments,
    update_payment_status
)


# -------------------------
# DRIVER: CREATE PAYMENT
# -------------------------
@driver_required
def payment_form(request):

    vehicle = Vehicle.objects.filter(assigned_driver=request.user).first()

    # 🚫 BLOCK if no vehicle assigned
    if not vehicle:
        messages.error(request, "You are not assigned to any vehicle. Contact admin.")
        return redirect('payment_list')

    if request.method == 'POST':

        amount = request.POST.get('amount')
        reference = request.POST.get('reference')
        phone_number = request.POST.get('phone_number')

        # 🔒 BASIC VALIDATION
        if not amount or not reference or not phone_number:
            messages.error(request, "All fields are required.")
            return redirect('payment_form')

        # 🔒 VALIDATE AMOUNT
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Enter a valid amount.")
            return redirect('payment_form')

        # 🔒 SIMPLE PHONE VALIDATION
        if not phone_number.startswith("07") or len(phone_number) != 10:
            messages.error(request, "Enter a valid phone number (07XXXXXXXX).")
            return redirect('payment_form')

        # 🔒 CREATE PAYMENT
        payment_data = {
            "driver": request.user,
            "vehicle": vehicle,
            "amount": amount,
            "reference": reference,
            "phone_number": phone_number,
            "status": "PENDING"
        }

        create_payment(payment_data)

        messages.success(request, "Payment submitted successfully and awaiting verification.")
        return redirect('payment_list')

    return render(request, 'payment_form.html', {
        'vehicle': vehicle
    })


# -------------------------
# DRIVER: VIEW PAYMENTS
# -------------------------
@driver_required
def payment_list(request):
    payments = get_driver_payments(request.user)

    return render(request, 'payment_list.html', {
        'payments': payments
    })


# -------------------------
# ADMIN: VIEW ALL PAYMENTS
# -------------------------
@admin_required
def admin_payment_list(request):
    payments = get_all_payments()

    return render(request, 'payment_list.html', {
        'payments': payments
    })


# -------------------------
# ADMIN: VERIFY PAYMENT
# -------------------------
@admin_required
def verify_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if payment.status == 'PENDING':
        update_payment_status(payment, 'SUCCESS')

        messages.success(request, "Payment verified successfully.")
    else:
        messages.warning(request, "Payment already processed.")

    return redirect('admin_payment_list')