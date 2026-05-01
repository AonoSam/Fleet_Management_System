import base64
import requests
from datetime import datetime
from django.conf import settings


class MpesaClient:

    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = settings.MPESA_ENVIRONMENT

        self.base_url = (
            "https://api.safaricom.co.ke"
            if self.environment == "production"
            else "https://sandbox.safaricom.co.ke"
        )

    # -------------------------
    # NORMALIZE PHONE (IMPORTANT FIX)
    # -------------------------
    def normalize_phone(self, phone):
        """
        Converts 07XXXXXXXX → 2547XXXXXXXX
        """
        if phone.startswith("0"):
            return "254" + phone[1:]
        if phone.startswith("+254"):
            return phone[1:]
        return phone

    # -------------------------
    # GET ACCESS TOKEN
    # -------------------------
    def get_access_token(self):

        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"

            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=10
            )

            response.raise_for_status()

            data = response.json()
            return data.get("access_token")

        except requests.exceptions.RequestException:
            return None

    # -------------------------
    # STK PUSH (PRODUCTION READY)
    # -------------------------
    def stk_push(self, phone_number, amount, reference, callback_url):

        try:
            access_token = self.get_access_token()

            if not access_token:
                return {
                    "success": False,
                    "message": "Unable to generate access token"
                }

            phone_number = self.normalize_phone(phone_number)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            password = base64.b64encode(
                (self.shortcode + self.passkey + timestamp).encode()
            ).decode()

            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": reference,
                "TransactionDesc": "Fleet System Payment"
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=15
            )

            data = response.json()

            # -------------------------
            # SUCCESS
            # -------------------------
            if data.get("ResponseCode") == "0":
                return {
                    "success": True,
                    "checkout_request_id": data.get("CheckoutRequestID"),
                    "merchant_request_id": data.get("MerchantRequestID"),
                    "message": "STK Push sent successfully"
                }

            # -------------------------
            # FAIL RESPONSE
            # -------------------------
            return {
                "success": False,
                "message": data.get("errorMessage", "STK Push failed"),
                "response_code": data.get("ResponseCode"),
                "raw": data
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Request timeout. Try again."
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Network error: {str(e)}"
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }