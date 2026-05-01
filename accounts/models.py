from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DRIVER', 'Driver'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='DRIVER'  # ✅ safe default
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True  # 🔥 important for Mpesa later
    )

    # 🔥 ACCOUNT STATUS (future-proofing)
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
        related_name='driver_profile'  # ✅ clean access: user.driver_profile
    )

    license_number = models.CharField(max_length=50, blank=True, null=True)

    contact = models.CharField(max_length=15, blank=True, null=True)

    performance_score = models.FloatField(default=0)

    # 🔥 OPTIONAL FINANCIAL TRACKING (useful later)
    total_loans_taken = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_repaid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return self.user.username