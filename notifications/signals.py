from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import Payment
from maintainance.models import MaintenanceSchedule
from loans.models import Loan
from accounts.models import User

from .services import create_notification


# -------------------------
# PAYMENT → ADMIN NOTIFICATION
# -------------------------
@receiver(post_save, sender=Payment)
def payment_notification(sender, instance, created, **kwargs):

    admins = User.objects.filter(role='ADMIN')

    if created:
        for admin in admins:
            create_notification(
                admin,
                f"New payment of KSh {instance.amount} submitted by {instance.driver}.",
                'PAYMENT'
            )

    elif instance.status == 'SUCCESS':
        for admin in admins:
            create_notification(
                admin,
                f"Payment of KSh {instance.amount} has been VERIFIED.",
                'PAYMENT'
            )


# -------------------------
# MAINTENANCE → DRIVER NOTIFICATION
# -------------------------
@receiver(post_save, sender=MaintenanceSchedule)
def maintenance_notification(sender, instance, created, **kwargs):

    vehicle = instance.vehicle

    if vehicle and vehicle.assigned_driver:

        driver = vehicle.assigned_driver

        if created:
            create_notification(
                driver,
                f"Maintenance scheduled for {vehicle.number_plate} on {instance.service_date}.",
                'MAINTENANCE'
            )

        if getattr(instance, 'completed', False):
            create_notification(
                driver,
                f"Maintenance completed for {vehicle.number_plate}.",
                'MAINTENANCE'
            )


# -------------------------
# LOAN → NOTIFICATION SYSTEM (NEW)
# -------------------------
@receiver(post_save, sender=Loan)
def loan_notification(sender, instance, created, **kwargs):

    # DRIVER LOAN
    if instance.loan_type == 'DRIVER' and instance.driver:

        if created:
            create_notification(
                instance.driver,
                f"Loan request of KSh {instance.amount} submitted.",
                'LOAN'
            )

        elif instance.status == 'APPROVED':
            create_notification(
                instance.driver,
                f"Your loan of KSh {instance.amount} has been APPROVED.",
                'LOAN'
            )

        elif instance.status == 'REJECTED':
            create_notification(
                instance.driver,
                f"Your loan of KSh {instance.amount} was REJECTED.",
                'LOAN'
            )

        elif instance.status == 'PAID':
            create_notification(
                instance.driver,
                f"Your loan of KSh {instance.amount} is fully PAID.",
                'LOAN'
            )

    # BANK LOAN → ADMIN ALERT
    if instance.loan_type == 'BANK':

        admins = User.objects.filter(role='ADMIN')

        for admin in admins:
            create_notification(
                admin,
                f"Bank loan of KSh {instance.amount} recorded in system.",
                'LOAN'
            )