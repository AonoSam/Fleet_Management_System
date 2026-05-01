from django.db import models
from accounts.models import User
from vehicles.models import Vehicle


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    license_number = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=15)

    assigned_vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    performance_score = models.FloatField(default=0)
    total_trips = models.PositiveIntegerField(default=0)
    total_collections = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return self.user.username


# 🔥 ADD THIS HELPER (IMPORTANT FOR REPORTS)
@property
def get_user(self):
    return self.user