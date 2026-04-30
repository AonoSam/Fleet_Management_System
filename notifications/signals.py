from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.models import Payment
from maintainance.models import MaintenanceSchedule
from accounts.models import User
from .models import Notification


# -------------------------
# HELPER
# -------------------------
def create_notification(user, message, n_type):
    Notification.objects.create(
        user=user,
        message=message,
        notification_type=n_type
    )


# -------------------------
# PAYMENT → NOTIFY ADMIN
# -------------------------
@receiver(post_save, sender=Payment)
def payment_notification(sender, instance, created, **kwargs):

    admin_users = User.objects.filter(role='ADMIN')

    if created:
        for admin in admin_users:
            create_notification(
                admin,
                f"New payment of KSh {instance.amount} submitted by {instance.driver.username}.",
                'PAYMENT'
            )

    elif instance.status == 'SUCCESS':
        for admin in admin_users:
            create_notification(
                admin,
                f"Payment of KSh {instance.amount} by {instance.driver.username} has been VERIFIED.",
                'PAYMENT'
            )


# -------------------------
# MAINTENANCE → NOTIFY DRIVER
# -------------------------
@receiver(post_save, sender=MaintenanceSchedule)
def maintenance_notification(sender, instance, created, **kwargs):

    vehicle = instance.vehicle

    if vehicle.assigned_driver:

        driver = vehicle.assigned_driver

        if created:
            create_notification(
                driver,
                f"Maintenance scheduled for {vehicle.number_plate} on {instance.service_date}",
                'MAINTENANCE'
            )

        if instance.completed:
            create_notification(
                driver,
                f"Maintenance completed for {vehicle.number_plate}",
                'MAINTENANCE'
            )