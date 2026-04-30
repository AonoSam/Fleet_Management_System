from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, DriverProfile


@receiver(post_save, sender=User)
def create_driver_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'DRIVER':
        DriverProfile.objects.create(user=instance)