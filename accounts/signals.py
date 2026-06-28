from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import User, DriverProfile, UserSession


# ── Auto-create DriverProfile when a DRIVER user is created ──
@receiver(post_save, sender=User)
def create_driver_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'DRIVER':
        DriverProfile.objects.create(user=instance)


# ── Record login time and IP ──
@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
    )
    UserSession.objects.create(
        user=user,
        ip_address=ip or None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        is_active=True,
    )


# ── Record logout time ──
@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    if user:
        session = UserSession.objects.filter(
            user=user, is_active=True
        ).order_by('-login_time').first()

        if session:
            session.logout_time = timezone.now()
            session.is_active   = False
            session.save()