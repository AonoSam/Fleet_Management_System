from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):

    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DRIVER', 'Driver'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='DRIVER'
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True
    )

    is_active_driver = models.BooleanField(default=True)

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_driver(self):
        return self.role == 'DRIVER'

    def __str__(self):
        return f"{self.username} ({self.role})"


# -------------------------
# DRIVER PROFILE
# -------------------------
class DriverProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )

    license_number = models.CharField(max_length=50, blank=True, null=True)
    contact        = models.CharField(max_length=15, blank=True, null=True)
    performance_score = models.FloatField(default=0)

    total_loans_taken = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_repaid      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    

    credit_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Unused overpayment credit available to apply to future loans."
    )

    def __str__(self):
        return self.user.username


# -------------------------
# USER SESSION TRACKING
# -------------------------
class UserSession(models.Model):

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.CharField(max_length=300, blank=True, null=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['-login_time']

    def duration(self):
        end = self.logout_time or timezone.now()
        delta = end - self.login_time
        minutes = int(delta.total_seconds() // 60)
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins  = minutes % 60
        return f"{hours}h {mins}m"

    def __str__(self):
        return f"{self.user.username} — {self.login_time.strftime('%Y-%m-%d %H:%M')}"