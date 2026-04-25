from django.shortcuts import render, redirect, get_object_or_404
from .models import Payment
from .services import get_all_payments, create_payment
from drivers.models import Driver
from .mpesa import MpesaClient


# =====================
# PAYMENT LIST
# =====================
def payment_list(request):
    payments = get_all_payments()
    return render(request, 'payment_list.html', {
        'payments': payments
    })


# =====================
# CREATE PAYMENT
# =====================
def payment_create(request):

    drivers = Driver.objects.all()

    if request.method == "POST":

        driver = get_object_or_404(Driver, id=request.POST.get('driver'))

        data = {
            "driver": driver,
            "amount": request.POST.get('amount'),
            "payment_method": request.POST.get('payment_method'),
            "transaction_code": request.POST.get('transaction_code')
        }

        payment = create_payment(data)

        # OPTIONAL: trigger Mpesa STK push
        if data["payment_method"] == "mpesa":
            mpesa = MpesaClient()
            mpesa.stk_push(driver.phone, data["amount"])

        return redirect('payment_list')

    return render(request, 'payment_form.html', {
        'drivers': drivers
    })


# =====================
# MPESA STATUS VIEW
# =====================
def mpesa_status(request):
    return render(request, 'mpesa_status.html')