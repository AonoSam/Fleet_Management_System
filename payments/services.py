from .models import Payment


def create_payment(data):
    return Payment.objects.create(**data)


def get_driver_payments(driver):
    return Payment.objects.filter(driver=driver).order_by('-created_at')


def update_payment_status(payment, status, receipt=None):
    payment.status = status
    if receipt:
        payment.mpesa_receipt = receipt
    payment.save()
    return payment