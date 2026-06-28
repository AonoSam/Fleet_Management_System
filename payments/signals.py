from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Payment
from notifications.models import Notification


def notify_admins(message, n_type='PAYMENT'):
    """Send a notification to every ADMIN user."""
    from accounts.models import User
    for admin in User.objects.filter(role='ADMIN'):
        Notification.objects.create(
            user=admin,
            message=message,
            notification_type=n_type
        )


@receiver(pre_save, sender=Payment)
def track_previous_status(sender, instance, **kwargs):
    """
    Before saving, remember what the status WAS so post_save
    can tell if it just changed to SUCCESS (vs. already being
    SUCCESS from a previous save — prevents duplicate alerts).
    """
    if instance.pk:
        try:
            instance._previous_status = Payment.objects.get(pk=instance.pk).status
        except Payment.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Payment)
def notify_admin_on_success(sender, instance, created, **kwargs):
    previous_status = getattr(instance, '_previous_status', None)

    # Only notify when status just BECAME 'SUCCESS'
    # (i.e. it wasn't SUCCESS before this save)
    if instance.status == 'SUCCESS' and previous_status != 'SUCCESS':
        driver_name = instance.driver.username if instance.driver else "Company"
        vehicle_plate = instance.vehicle.number_plate if instance.vehicle else "—"

        message = (
            f"✅ Payment confirmed: KES {instance.amount} from {driver_name} "
            f"({vehicle_plate}) — Ref: {instance.mpesa_receipt or instance.reference}"
        )

        notify_admins(message, n_type='PAYMENT')