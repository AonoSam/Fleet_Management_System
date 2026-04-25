import requests


class MpesaClient:

    def __init__(self):
        self.consumer_key = "YOUR_KEY"
        self.consumer_secret = "YOUR_SECRET"
        self.base_url = "https://sandbox.safaricom.co.ke"

    def stk_push(self, phone, amount):
        """
        Placeholder for STK Push
        """
        print(f"Sending STK Push to {phone} for {amount}")

        # Later we integrate real Daraja API here
        return {
            "status": "success",
            "message": "STK push initiated (mock)"
        }