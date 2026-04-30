from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaintenanceSchedule
from notifications.models import Notification


def create_notification(user, message, n_type):
    Notification.objects.create(
        user=user,
        message=message,
        notification_type=n_type
    )


@receiver(post_save, sender=MaintenanceSchedule)
def maintenance_notification(sender, instance, created, **kwargs):

    vehicle = instance.vehicle

    if not vehicle.assigned_driver:
        return

    driver = vehicle.assigned_driver

    # When admin creates schedule
    if created:
        create_notification(
            driver,
            f"Maintenance scheduled for {vehicle.number_plate} on {instance.service_date}",
            'MAINTENANCE'
        )

    # When admin marks completed
    if instance.completed:
        create_notification(
            driver,
            f"Maintenance completed for {vehicle.number_plate}",
            'MAINTENANCE'
        )