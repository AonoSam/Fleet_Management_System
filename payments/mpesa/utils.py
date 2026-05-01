from .client import MpesaClient


def initiate_stk_push(phone, amount, reference, callback_url):
    """
    Clean wrapper for MPESA STK Push
    Ensures consistent response format across system
    """

    try:
        client = MpesaClient()

        response = client.stk_push(
            phone_number=phone,
            amount=amount,
            reference=reference,
            callback_url=callback_url
        )

        # -------------------------
        # STANDARDIZE RESPONSE
        # -------------------------
        if isinstance(response, dict):

            if response.get("success"):
                return {
                    "success": True,
                    "checkout_request_id": response.get("checkout_request_id"),
                    "merchant_request_id": response.get("merchant_request_id"),
                    "message": response.get("message")
                }

            return {
                "success": False,
                "message": response.get("message", "STK Push failed"),
                "raw": response
            }

        return {
            "success": False,
            "message": "Invalid MPESA response format"
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }