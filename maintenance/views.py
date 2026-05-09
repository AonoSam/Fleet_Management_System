from django.shortcuts import render, redirect, get_object_or_404
from accounts.permissions import admin_required, driver_required
from vehicles.models import Vehicle
from maintenance.models import MaintenanceSchedule, RepairLog
from maintenance.services import get_schedules, get_repairs


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
# MARK COMPLETE + REPAIR LOG
# -------------------------
@admin_required
def mark_complete(request, pk):
    schedule = get_object_or_404(MaintenanceSchedule, id=pk)

    if request.method == 'POST':
        cost = request.POST.get('cost')

        schedule.completed = True
        schedule.save()

        RepairLog.objects.create(
            vehicle=schedule.vehicle,
            issue=schedule.description,
            cost=float(cost) if cost else 0,
            repaired_on=schedule.service_date,
            progress='COMPLETED',
            category='GENERAL',
        )

        return redirect('schedule_list')

    return render(request, 'mark_complete.html', {'schedule': schedule})


# -------------------------
# ADMIN: REPAIR LOGS LIST
# -------------------------
@admin_required
def repair_logs(request):
    repairs = RepairLog.objects.select_related('vehicle').all()

    # Optional filters
    vehicle_id = request.GET.get('vehicle')
    category   = request.GET.get('category')
    progress   = request.GET.get('progress')

    if vehicle_id:
        repairs = repairs.filter(vehicle_id=vehicle_id)
    if category:
        repairs = repairs.filter(category=category)
    if progress:
        repairs = repairs.filter(progress=progress)

    vehicles = Vehicle.objects.all()

    return render(request, 'repair_logs.html', {
        'repairs':            repairs,
        'vehicles':           vehicles,
        'category_choices':   RepairLog.CATEGORY_CHOICES,
        'progress_choices':   RepairLog.PROGRESS_CHOICES,
        'selected_vehicle':   vehicle_id,
        'selected_category':  category,
        'selected_progress':  progress,
    })


# -------------------------
# ADMIN: ADD REPAIR
# -------------------------
@admin_required
def add_repair(request):
    vehicles = Vehicle.objects.all()

    if request.method == 'POST':
        RepairLog.objects.create(
            vehicle_id  = request.POST.get('vehicle'),
            category    = request.POST.get('category'),
            issue       = request.POST.get('issue'),
            mechanic    = request.POST.get('mechanic') or None,
            cost        = float(request.POST.get('cost') or 0),
            progress    = request.POST.get('progress', 'PENDING'),
            repaired_on = request.POST.get('repaired_on') or None,
        )
        return redirect('repair_logs')

    return render(request, 'repair_form.html', {
        'vehicles':         vehicles,
        'category_choices': RepairLog.CATEGORY_CHOICES,
        'progress_choices': RepairLog.PROGRESS_CHOICES,
    })


# -------------------------
# ADMIN: EDIT REPAIR
# -------------------------
@admin_required
def edit_repair(request, pk):
    repair   = get_object_or_404(RepairLog, pk=pk)
    vehicles = Vehicle.objects.all()

    if request.method == 'POST':
        repair.vehicle_id  = request.POST.get('vehicle')
        repair.category    = request.POST.get('category')
        repair.issue       = request.POST.get('issue')
        repair.mechanic    = request.POST.get('mechanic') or None
        repair.cost        = float(request.POST.get('cost') or 0)
        repair.progress    = request.POST.get('progress', repair.progress)
        repair.repaired_on = request.POST.get('repaired_on') or None
        repair.save()
        return redirect('repair_logs')

    return render(request, 'repair_form.html', {
        'repair':           repair,
        'vehicles':         vehicles,
        'category_choices': RepairLog.CATEGORY_CHOICES,
        'progress_choices': RepairLog.PROGRESS_CHOICES,
    })


# -------------------------
# ADMIN: DELETE REPAIR
# -------------------------
@admin_required
def delete_repair(request, pk):
    repair = get_object_or_404(RepairLog, pk=pk)
    if request.method == 'POST':
        repair.delete()
        return redirect('repair_logs')
    return render(request, 'repair_confirm_delete.html', {'repair': repair})


# -------------------------
# ADMIN: REPAIR DETAIL
# -------------------------
@admin_required
def repair_detail(request, pk):
    repair = get_object_or_404(RepairLog.objects.select_related('vehicle'), pk=pk)
    return render(request, 'repair_detail.html', {'repair': repair})


# -------------------------
# DRIVER VIEW
# -------------------------
@driver_required
def my_maintenance(request):
    schedules = MaintenanceSchedule.objects.filter(
        vehicle__assigned_driver=request.user
    )
    repairs = RepairLog.objects.filter(
        vehicle__assigned_driver=request.user
    )
    return render(request, 'my_maintenance.html', {
        'schedules': schedules,
        'repairs':   repairs,
    })