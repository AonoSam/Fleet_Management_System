from django.shortcuts import render, redirect, get_object_or_404
from accounts.permissions import admin_required, driver_required
from vehicles.models import Vehicle
from .models import MaintenanceSchedule, RepairLog
from .services import get_schedules, get_repairs


# -------------------------
# ADMIN: VIEW SCHEDULES
# -------------------------
@admin_required
def schedule_list(request):
    schedules = get_schedules()
    return render(request, 'schedule_list.html', {'schedules': schedules})


# -------------------------
# ADMIN: CREATE SCHEDULE
# -------------------------
@admin_required
def schedule_create(request):
    vehicles = Vehicle.objects.all()

    if request.method == 'POST':
        MaintenanceSchedule.objects.create(
            vehicle_id=request.POST.get('vehicle'),
            service_date=request.POST.get('service_date'),
            description=request.POST.get('description')
        )
        return redirect('schedule_list')

    return render(request, 'schedule_form.html', {'vehicles': vehicles})


# -------------------------
# ✅ UPDATED: MARK COMPLETE + CREATE REPAIR LOG
# -------------------------
@admin_required
def mark_complete(request, pk):
    schedule = get_object_or_404(MaintenanceSchedule, id=pk)

    if request.method == 'POST':
        cost = request.POST.get('cost')

        # mark completed
        schedule.completed = True
        schedule.save()

        # 🔥 create repair log automatically
        RepairLog.objects.create(
            vehicle=schedule.vehicle,
            issue=schedule.description,
            cost=cost or 0,
            repaired_on=schedule.service_date
        )

        return redirect('schedule_list')

    # show form to input cost
    return render(request, 'mark_complete.html', {'schedule': schedule})


# -------------------------
# ADMIN: REPAIR LOGS
# -------------------------
@admin_required
def repair_logs(request):
    repairs = get_repairs()
    return render(request, 'repair_logs.html', {'repairs': repairs})


# -------------------------
# ADMIN: ADD REPAIR (manual)
# -------------------------
@admin_required
def add_repair(request):
    vehicles = Vehicle.objects.all()

    if request.method == 'POST':
        RepairLog.objects.create(
            vehicle_id=request.POST.get('vehicle'),
            issue=request.POST.get('issue'),
            cost=request.POST.get('cost'),
            repaired_on=request.POST.get('repaired_on')  # ✅ added date
        )
        return redirect('repair_logs')

    return render(request, 'repair_form.html', {'vehicles': vehicles})


# -------------------------
# DRIVER: VIEW THEIR VEHICLE SCHEDULES
# -------------------------
@driver_required
def my_maintenance(request):
    schedules = MaintenanceSchedule.objects.filter(
        vehicle__assigned_driver=request.user
    )

    return render(request, 'schedule_list.html', {'schedules': schedules})