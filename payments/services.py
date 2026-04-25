from .models import Payment


def get_all_payments():
    return Payment.objects.all().order_by('-payment_date')


def create_payment(data):
    return Payment.objects.create(**data)


def get_driver_payments(driver):
    return Payment.objects.filter(driver=driver)