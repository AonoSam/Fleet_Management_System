from .models import Vehicle


def get_all_vehicles():
    return Vehicle.objects.select_related('assigned_driver').all()


def get_vehicle(vehicle_id):
    return Vehicle.objects.get(id=vehicle_id)


def create_vehicle(data):
    return Vehicle.objects.create(**data)


def update_vehicle(vehicle, data):
    for key, value in data.items():
        setattr(vehicle, key, value)
    vehicle.save()
    return vehicle


def delete_vehicle(vehicle):
    vehicle.delete()