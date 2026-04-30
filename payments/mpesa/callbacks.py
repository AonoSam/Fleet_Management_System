from payments.models import Payment


def mpesa_callback(data):
    """
    Handles Mpesa response
    """

    reference = data.get('reference')
    status = data.get('status')
    receipt = data.get('receipt')

    try:
        payment = Payment.objects.get(reference=reference)
        payment.status = status
        payment.mpesa_receipt = receipt
        payment.save()
    except Payment.DoesNotExist:
        pass