from django.db import models
from accounts.models import User


class Vehicle(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('INACTIVE', 'Inactive'),
    )

    number_plate = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    assigned_driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'DRIVER'}
    )

    def __str__(self):
        return f"{self.number_plate} - {self.model}"