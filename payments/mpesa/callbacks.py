import json
from django.http import JsonResponse

from payments.models import Payment
from payments.services import update_payment_status
from loans.services import record_repayment


def mpesa_callback(request):

    try:
        data = json.loads(request.body.decode('utf-8'))
        result = data.get("Body", {}).get("stkCallback", {})

        checkout_id = result.get("CheckoutRequestID")
        result_code = result.get("ResultCode")

        if not checkout_id:
            return JsonResponse({"error": "Missing CheckoutRequestID"})

        # -------------------------
        # FIND PAYMENT
        # -------------------------
        payment = Payment.objects.filter(reference=checkout_id).first()

        if not payment:
            return JsonResponse({"Result": "Payment not found"})

        # -------------------------
        # IDEMPOTENCY (NO DOUBLE PROCESS)
        # -------------------------
        if payment.status == "SUCCESS":
            return JsonResponse({"Result": "Already processed"})

        # -------------------------
        # ❌ FAILED / CANCELLED / TIMEOUT
        # -------------------------
        if result_code != 0:

            # 🔥 DELETE FAILED PAYMENT (CRITICAL FIX)
            payment.delete()

            return JsonResponse({"Result": "FAILED - DELETED"})

        # -------------------------
        # ✅ SUCCESS TRANSACTION
        # -------------------------
        metadata = result.get("CallbackMetadata", {}).get("Item", [])

        receipt = None
        amount = 0

        for item in metadata:
            name = item.get("Name")

            if name == "MpesaReceiptNumber":
                receipt = item.get("Value")

            elif name == "Amount":
                amount = float(item.get("Value", 0))

        # -------------------------
        # UPDATE PAYMENT
        # -------------------------
        update_payment_status(payment, "SUCCESS", receipt=receipt)

        # -------------------------
        # AUTO LOAN REPAYMENT (SAFE)
        # -------------------------
        if payment.payment_type == "LOAN_REPAYMENT" and payment.loan:

            # 🔥 DOUBLE SAFETY (VERY IMPORTANT)
            if payment.loan and payment.status == "SUCCESS":
                record_repayment(payment.loan, amount)

        return JsonResponse({"Result": "OK"})

    except Exception as e:
        return JsonResponse({"error": str(e)})