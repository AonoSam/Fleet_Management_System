from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .models import Driver
from .services import create_driver, get_all_drivers, get_driver
from vehicles.models import Vehicle

User = get_user_model()


# =====================
# DRIVER LIST
# =====================
def driver_list(request):
    drivers = get_all_drivers()
    return render(request, 'driver_list.html', {'drivers': drivers})


# =====================
# CREATE DRIVER
# =====================
def driver_create(request):

    vehicles = Vehicle.objects.all()

    if request.method == "POST":

        # ✅ CREATE USER USING CUSTOM USER MODEL
        user = User.objects.create_user(
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        data = {
            "license_number": request.POST.get('license_number'),
            "phone": request.POST.get('phone'),
            "vehicle": Vehicle.objects.get(id=request.POST.get('vehicle')) 
                        if request.POST.get('vehicle') else None
        }

        create_driver(user, data)
        return redirect('driver_list')

    return render(request, 'driver_form.html', {
        'vehicles': vehicles
    })


# =====================
# PERFORMANCE PAGE
# =====================
def performance_view(request, pk):
    driver = get_driver(pk)
    return render(request, 'performance.html', {
        'driver': driver
    })