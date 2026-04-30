from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DRIVER', 'Driver'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_driver(self):
        return self.role == 'DRIVER'

    def __str__(self):
        return f"{self.username} ({self.role})"


class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    contact = models.CharField(max_length=15, blank=True, null=True)
    performance_score = models.FloatField(default=0)

    def __str__(self):
        return self.user.username