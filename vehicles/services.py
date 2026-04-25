from .models import Vehicle

def create_vehicle(data):
    return Vehicle.objects.create(**data)


def get_all_vehicles():
    return Vehicle.objects.all()


def get_vehicle(vehicle_id):
    return Vehicle.objects.get(id=vehicle_id)