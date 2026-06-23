from .models import MaintenanceSchedule, RepairLog, VehicleMaintenancePlan


def get_schedules():
    return MaintenanceSchedule.objects.select_related('vehicle').all()


def get_repairs():
    return RepairLog.objects.select_related('vehicle').all()


def get_maintenance_plans():
    return VehicleMaintenancePlan.objects.select_related('vehicle').all()


def get_or_create_plan(vehicle, interval_days=90, description="Routine scheduled maintenance"):
    plan, created = VehicleMaintenancePlan.objects.get_or_create(
        vehicle=vehicle,
        defaults={
            'interval_days': interval_days,
            'default_description': description,
        }
    )
    return plan