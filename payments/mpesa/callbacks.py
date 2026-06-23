from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from payments.models import Payment
from payments.services import update_payment_status
from loans.services import record_repayment


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
        amount  = 0

        for item in metadata:
            name = item.get("Name")
            if name == "MpesaReceiptNumber":
                receipt = item.get("Value")
            elif name == "Amount":
                amount = float(item.get("Value", 0))

        # ── Update payment ──
        update_payment_status(payment, "SUCCESS", receipt=receipt)

        # ── Auto loan repayment ──
        if payment.payment_type == "LOAN_REPAYMENT" and payment.loan:
            record_repayment(payment.loan, amount)

        return JsonResponse({"Result": "OK"})

    except Exception as e:
        import traceback
        traceback.print_exc()  # shows full error in Django terminal
        return JsonResponse({"error": str(e)})