from .models import MaintenanceSchedule, RepairLog


def get_schedules():
    return MaintenanceSchedule.objects.all().order_by('-due_date')


def create_schedule(data):
    return MaintenanceSchedule.objects.create(**data)


def get_repairs():
    return RepairLog.objects.all().order_by('-repair_date')


def create_repair(data):
    return RepairLog.objects.create(**data)