from .models import Payment


# -------------------------
# CREATE PAYMENT (SAFE)
# -------------------------
def create_payment(data):
    """
    Central payment creation logic
    """
    return Payment.objects.create(**data)


# -------------------------
# DRIVER PAYMENTS
# -------------------------
def get_driver_payments(driver):
    return Payment.objects.filter(
        driver=driver
    ).order_by('-created_at')


# -------------------------
# ALL PAYMENTS (ADMIN)
# -------------------------
def get_all_payments():
    return Payment.objects.all().order_by('-created_at')


# -------------------------
# UPDATE PAYMENT STATUS
# -------------------------
def update_payment_status(payment, status, receipt=None):
    payment.status = status

    if receipt:
        payment.mpesa_receipt = receipt

    payment.save()
    return payment