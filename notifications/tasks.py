from vehicles.models import Vehicle
from maintainance.models import MaintenanceSchedule
from drivers.models import Driver
from django.utils import timezone

from .services import create_notification


# =========================
# MAINTENANCE ALERT CHECK
# =========================
def check_maintenance_alerts():

    today = timezone.now().date()
    upcoming = MaintenanceSchedule.objects.filter(is_completed=False)

    for item in upcoming:
        if item.due_date == today:

            # Notify admin or assigned driver
            if item.vehicle:
                drivers = Driver.objects.filter(vehicle=item.vehicle)

                for d in drivers:
                    create_notification(
                        user=d.user,
                        title="Maintenance Due Today",
                        message=f"Vehicle {item.vehicle} requires {item.service_type} today.",
                        notification_type="maintenance"
                    )


# =========================
# PAYMENT ALERT (FUTURE USE)
# =========================
def payment_alert(user, amount):
    create_notification(
        user=user,
        title="Payment Received",
        message=f"You received KSH {amount}",
        notification_type="payment"
    )