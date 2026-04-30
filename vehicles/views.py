from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle
from .services import get_all_vehicles, get_vehicle
from accounts.models import User
from accounts.permissions import admin_required


@admin_required
def vehicle_list(request):
    vehicles = get_all_vehicles()
    return render(request, 'vehicle_list.html', {'vehicles': vehicles})


@admin_required
def vehicle_create(request):
    drivers = User.objects.filter(role='DRIVER')

    if request.method == 'POST':
        Vehicle.objects.create(
            number_plate=request.POST.get('number_plate'),
            model=request.POST.get('model'),
            year=request.POST.get('year'),
            status=request.POST.get('status'),
            assigned_driver_id=request.POST.get('assigned_driver') or None
        )
        return redirect('vehicle_list')

    return render(request, 'vehicle_form.html', {'drivers': drivers})


@admin_required
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    drivers = User.objects.filter(role='DRIVER')

    if request.method == 'POST':
        vehicle.number_plate = request.POST.get('number_plate')
        vehicle.model = request.POST.get('model')
        vehicle.year = request.POST.get('year')
        vehicle.status = request.POST.get('status')
        vehicle.assigned_driver_id = request.POST.get('assigned_driver') or None
        vehicle.save()

        return redirect('vehicle_list')

    return render(request, 'vehicle_form.html', {
        'vehicle': vehicle,
        'drivers': drivers
    })


@admin_required
def vehicle_detail(request, pk):
    vehicle = get_vehicle(pk)
    return render(request, 'vehicle_detail.html', {'vehicle': vehicle})


@admin_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    vehicle.delete()
    return redirect('vehicle_list')