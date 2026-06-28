from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import traceback
from decimal import Decimal

from payments.models import Payment
from payments.services import update_payment_status
from loans.services import record_repayment


def _safe_record_repayment(loan, amount, source='MPESA'):
    """
    Calls record_repayment with a source kwarg if the function
    supports it, otherwise falls back to the 2-argument call.
    This avoids a hard crash if loans/services.py hasn't been
    updated yet to accept the source parameter.
    """
    try:
        return record_repayment(loan, amount, source=source)
    except TypeError:
        return record_repayment(loan, amount)


@csrf_exempt
def mpesa_callback(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        result = data.get("Body", {}).get("stkCallback", {})

        checkout_id = result.get("CheckoutRequestID")
        result_code = result.get("ResultCode")

        if not checkout_id:
            return JsonResponse({"error": "Missing CheckoutRequestID"})

        payment = Payment.objects.filter(reference=checkout_id).first()

        if not payment:
            return JsonResponse({"Result": "Payment not found"})

        if payment.status == "SUCCESS":
            return JsonResponse({"Result": "Already processed"})

        if result_code != 0:
            payment.status = "FAILED"
            payment.save(update_fields=['status'])
            return JsonResponse({"Result": "FAILED"})

        # ── Parse metadata ──
        metadata = result.get("CallbackMetadata", {}).get("Item", [])
        receipt = None
        amount = 0

        for item in metadata:
            name = item.get("Name")
            if name == "MpesaReceiptNumber":
                receipt = item.get("Value")
            elif name == "Amount":
                amount = float(item.get("Value", 0))

        # ── Update payment ──
        update_payment_status(payment, "SUCCESS", receipt=receipt)

        # ── Auto loan repayment + overpayment crediting ──
        if payment.payment_type == "LOAN_REPAYMENT" and payment.loan:
            from accounts.models import DriverProfile

            loan = payment.loan
            amount_decimal = Decimal(str(amount))
            balance_before = loan.balance()

            if amount_decimal > balance_before and loan.driver:
                # Overpayment via M-Pesa — settle the loan fully,
                # bank the excess as credit
                excess = amount_decimal - balance_before

                if balance_before > 0:
                    _safe_record_repayment(loan, balance_before)

                profile, _ = DriverProfile.objects.get_or_create(user=loan.driver)
                profile.credit_balance += excess
                profile.save(update_fields=['credit_balance'])
            else:
                _safe_record_repayment(loan, amount_decimal)

        return JsonResponse({"Result": "OK"})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)})