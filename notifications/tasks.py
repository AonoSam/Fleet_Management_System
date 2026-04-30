from django.utils import timezone
from maintainance.models import MaintenanceSchedule
from .services import create_notification


def upcoming_maintenance_alerts():
    today = timezone.now().date()

    schedules = MaintenanceSchedule.objects.filter(
        service_date=today,
        completed=False
    )

    for s in schedules:
        if s.vehicle.assigned_driver:
            create_notification(
                s.vehicle.assigned_driver,
                f"Reminder: Maintenance for {s.vehicle} is scheduled today.",
                'MAINTENANCE'
            )