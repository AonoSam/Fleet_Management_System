from .models import Driver


def create_driver(user, data):
    return Driver.objects.create(
        user=user,
        license_number=data.get('license_number'),
        phone=data.get('phone'),
        vehicle=data.get('vehicle'),
    )


def get_all_drivers():
    return Driver.objects.all()


def get_driver(driver_id):
    return Driver.objects.get(id=driver_id)