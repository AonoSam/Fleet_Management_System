from django.shortcuts import render, redirect
from vehicles.models import Vehicle
from .services import get_schedules, create_schedule, get_repairs, create_repair


# =====================
# SCHEDULE LIST
# =====================
def schedule_list(request):
    schedules = get_schedules()
    return render(request, 'schedule_list.html', {
        'schedules': schedules
    })


# =====================
# CREATE SCHEDULE
# =====================
def schedule_create(request):

    vehicles = Vehicle.objects.all()

    if request.method == "POST":

        data = {
            "vehicle": Vehicle.objects.get(id=request.POST.get('vehicle')),
            "service_type": request.POST.get('service_type'),
            "description": request.POST.get('description'),
            "due_date": request.POST.get('due_date'),
        }

        create_schedule(data)
        return redirect('schedule_list')

    return render(request, 'schedule_form.html', {
        'vehicles': vehicles
    })


# =====================
# REPAIR LOGS
# =====================
def repair_logs(request):
    repairs = get_repairs()
    return render(request, 'repair_logs.html', {
        'repairs': repairs
    })


# =====================
# CREATE REPAIR
# =====================
def repair_create(request):

    vehicles = Vehicle.objects.all()

    if request.method == "POST":

        data = {
            "vehicle": Vehicle.objects.get(id=request.POST.get('vehicle')),
            "issue": request.POST.get('issue'),
            "cost": request.POST.get('cost'),
            "repaired_by": request.POST.get('repaired_by'),
            "repair_date": request.POST.get('repair_date'),
            "notes": request.POST.get('notes'),
        }

        create_repair(data)
        return redirect('repair_logs')

    return render(request, 'schedule_form.html', {
        'vehicles': vehicles
    })