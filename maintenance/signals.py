from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaintenanceSchedule
from notifications.models import Notification


def create_notification(user, message, n_type):
    if user:
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=n_type
        )


def notify_admins(message, n_type):
    """Send a notification to every ADMIN user."""
    from accounts.models import User
    for admin in User.objects.filter(role='ADMIN'):
        create_notification(admin, message, n_type)


@receiver(post_save, sender=MaintenanceSchedule)
def maintenance_notification(sender, instance, created, **kwargs):

    vehicle = instance.vehicle
    driver = vehicle.assigned_driver if vehicle.assigned_driver else None

    # When a new schedule is created
    if created:
        msg = f"Maintenance scheduled for {vehicle.number_plate} on {instance.service_date}"
        if driver:
            create_notification(driver, msg, 'MAINTENANCE')
        notify_admins(msg, 'MAINTENANCE')

    # When marked completed: notify + auto-generate next schedule
    if instance.completed:
        msg = f"Maintenance completed for {vehicle.number_plate}"
        if driver:
            create_notification(driver, msg, 'MAINTENANCE')
        notify_admins(msg, 'MAINTENANCE')

        plan = getattr(vehicle, 'maintenance_plan', None)
        if plan and plan.is_active:
            plan.last_scheduled_date = instance.service_date
            plan.save(update_fields=['last_scheduled_date'])
            plan.generate_next_schedule()