from decimal import Decimal
from django.conf import settings

from .models import Payment
from .mpesa.client import MpesaClient
from loans.services import record_repayment


# -------------------------
# CREATE PAYMENT (CORE)
# -------------------------
def create_payment(data):
    """
    Creates payment + immediately triggers MPESA STK push
    """

    payment = Payment.objects.create(**data)

    # 🔥 AUTO INITIATE MPESA
    initiate_mpesa_payment(payment)

    return payment


# -------------------------
# INITIATE MPESA PAYMENT
# -------------------------
def initiate_mpesa_payment(payment):

    client = MpesaClient()

    response = client.stk_push(
        phone_number=payment.phone_number,
        amount=payment.amount,
        reference=payment.reference,
        callback_url=settings.MPESA_CALLBACK_URL
    )

    # Save checkout request id for callback matching
    try:
        checkout_id = response.get("CheckoutRequestID")
        if checkout_id:
            payment.reference = checkout_id
            payment.save(update_fields=["reference"])
    except Exception:
        pass

    return response


# -------------------------
# DRIVER PAYMENTS
# -------------------------
def get_driver_payments(driver):
    return Payment.objects.filter(driver=driver).order_by('-created_at')


# -------------------------
# ALL PAYMENTS (ADMIN)
# -------------------------
def get_all_payments():
    return Payment.objects.all().order_by('-created_at')


# -------------------------
# UPDATE STATUS (MANUAL + CALLBACK)
# -------------------------
def update_payment_status(payment, status, receipt=None):

    payment.status = status

    if receipt:
        payment.mpesa_receipt = receipt

    payment.save(update_fields=['status', 'mpesa_receipt'])

    return payment


# -------------------------
# LINK PAYMENT TO LOAN
# -------------------------
def link_payment_to_loan(payment, loan):

    payment.loan = loan
    payment.payment_type = "LOAN_REPAYMENT"
    payment.save(update_fields=['loan', 'payment_type'])

    return payment


# -------------------------
# CONFIRM MPESA SUCCESS FLOW (IMPORTANT 🔥)
# -------------------------
def confirm_mpesa_payment(payment, receipt, amount=None):

    payment.status = "SUCCESS"
    payment.mpesa_receipt = receipt

    if amount:
        payment.amount = Decimal(amount)

    payment.save()

    # 🔥 AUTO APPLY TO LOAN IF EXISTS
    if payment.loan:
        record_repayment(payment.loan, payment.amount)

    return payment


# -------------------------
# SUMMARY
# -------------------------
def get_payment_summary():

    return {
        "total_payments": Payment.objects.count(),
        "success": Payment.objects.filter(status="SUCCESS").count(),
        "pending": Payment.objects.filter(status="PENDING").count(),
        "failed": Payment.objects.filter(status="FAILED").count(),
    }