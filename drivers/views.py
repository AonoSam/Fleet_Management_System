from django.shortcuts import render, redirect, get_object_or_404
from .models import Driver
from vehicles.models import Vehicle
from accounts.permissions import admin_required, driver_required
from .services import get_all_drivers
from payments.models import Payment
from django.db.models import Sum, Q
from accounts.models import User


# -------------------------
# DRIVER LIST
# -------------------------
@admin_required
def driver_list(request):
    drivers = get_all_drivers()
    return render(request, 'driver_list.html', {'drivers': drivers})


# -------------------------
# CREATE DRIVER
# -------------------------
@admin_required
def driver_create(request):
    # FIXED: correct vehicle filtering (no broken QuerySet inside Q)
    vehicles = Vehicle.objects.filter(
        Q(assigned_driver__isnull=True) | Q(assigned_driver__isnull=False)
    )

    users = User.objects.filter(role='DRIVER')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.filter(id=user_id, role='DRIVER').first()

        if not user:
            return redirect('driver_create')

        if Driver.objects.filter(user=user).exists():
            return redirect('driver_list')

        Driver.objects.create(
            user=user,
            license_number=request.POST.get('license_number'),
            phone=request.POST.get('phone'),
            assigned_vehicle_id=request.POST.get('assigned_vehicle') or None
        )

        return redirect('driver_list')

    return render(request, 'driver_form.html', {
        'vehicles': vehicles,
        'users': users
    })


# -------------------------
# UPDATE DRIVER
# -------------------------
@admin_required
def driver_update(request, pk):
    driver = get_object_or_404(Driver, pk=pk)

    vehicles = Vehicle.objects.filter(
        Q(assigned_driver__isnull=True) | Q(assigned_driver=driver.user)
    )

    users = User.objects.filter(role='DRIVER')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.filter(id=user_id, role='DRIVER').first()

        if user:
            driver.user = user

        driver.license_number = request.POST.get('license_number')
        driver.phone = request.POST.get('phone')
        driver.assigned_vehicle_id = request.POST.get('assigned_vehicle') or None
        driver.save()

        return redirect('driver_list')

    return render(request, 'driver_form.html', {
        'driver': driver,
        'vehicles': vehicles,
        'users': users
    })


# -------------------------
# DELETE DRIVER (FIXED ERROR)
# -------------------------
@admin_required
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)

    if request.method == 'POST':
        driver.delete()
        return redirect('driver_list')

    # safety confirmation page fallback
    return render(request, 'driver_confirm_delete.html', {
        'driver': driver
    })


# -------------------------
# PERFORMANCE
# -------------------------
@admin_required
def driver_performance(request, pk):
    driver = get_object_or_404(Driver, pk=pk)

    payments = Payment.objects.filter(
        driver=driver.user,
        status='SUCCESS'
    )

    total_collections = payments.aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_trips = payments.count()
    performance_score = float(total_trips)

    return render(request, 'performance.html', {
        'driver': driver,
        'total_collections': total_collections,
        'total_trips': total_trips,
        'performance_score': performance_score,
    })


# -------------------------
# DRIVER VIEW VEHICLE
# -------------------------
@driver_required
def my_vehicle(request):
    vehicle = Vehicle.objects.filter(
        assigned_driver=request.user
    ).first()

    return render(request, 'my_vehicle.html', {
        'vehicle': vehicle
    })