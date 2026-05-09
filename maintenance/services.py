from .models import MaintenanceSchedule, RepairLog


def get_schedules():
    return MaintenanceSchedule.objects.select_related('vehicle').all()


def get_repairs():
    return RepairLog.objects.select_related('vehicle').all()