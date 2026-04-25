from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle
from .services import create_vehicle, get_all_vehicles, get_vehicle


# =========================
# VEHICLE LIST
# =========================
def vehicle_list(request):
    vehicles = get_all_vehicles()
    return render(request, 'vehicle_list.html', {'vehicles': vehicles})


# =========================
# CREATE VEHICLE
# =========================
def vehicle_create(request):

    if request.method == "POST":
        data = {
            "number_plate": request.POST.get("number_plate"),
            "model": request.POST.get("model"),
            "year": request.POST.get("year"),
            "status": request.POST.get("status"),
        }

        create_vehicle(data)
        return redirect('vehicle_list')

    return render(request, 'vehicle_forms.html')


# =========================
# VEHICLE DETAIL
# =========================
def vehicle_detail(request, pk):
    vehicle = get_vehicle(pk)
    return render(request, 'vehicle_detail.html', {'vehicle': vehicle})