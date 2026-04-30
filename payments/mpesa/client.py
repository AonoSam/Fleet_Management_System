import requests


def stk_push(phone, amount, reference):
    # 🔥 Simplified structure (you later plug real Safaricom API)
    payload = {
        "phone": phone,
        "amount": amount,
        "reference": reference
    }

    print("STK PUSH INITIATED:", payload)

    return {
        "status": "success",
        "message": "STK push simulated"
    }