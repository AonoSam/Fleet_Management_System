from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.permissions import driver_required, admin_required
from vehicles.models import Vehicle
from .models import Payment
from .services import create_payment, get_driver_payments


# 👨‍✈️ DRIVER SEND PAYMENT REQUEST
@driver_required
def payment_form(request):

    vehicle = Vehicle.objects.filter(assigned_driver=request.user).first()

    if request.method == 'POST':
        Payment.objects.create(
            driver=request.user,
            vehicle=vehicle,
            amount=request.POST.get('amount'),
            reference=request.POST.get('reference'),
            phone_number=request.POST.get('phone_number'),
            status='PENDING'   # 🔥 ensure always starts as pending
        )
        return redirect('payment_list')

    return render(request, 'payment_form.html', {'vehicle': vehicle})


# 👨‍✈️ DRIVER VIEW PAYMENTS
@driver_required
def payment_list(request):
    payments = get_driver_payments(request.user)
    return render(request, 'payment_list.html', {'payments': payments})


# 🔵 ADMIN VIEW ALL PAYMENTS
@admin_required
def admin_payment_list(request):
    payments = Payment.objects.all().order_by('-created_at')
    return render(request, 'payment_list.html', {'payments': payments})


# 🔥 ADMIN VERIFY PAYMENT
@admin_required
def verify_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if payment.status == 'PENDING':
        payment.status = 'SUCCESS'   # SUCCESS = VERIFIED
        payment.save()
        messages.success(request, "Payment verified successfully.")
    else:
        messages.warning(request, "Payment already processed.")

    return redirect('admin_payment_list')