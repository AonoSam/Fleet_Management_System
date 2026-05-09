from django.db import models
from vehicles.models import Vehicle


class MaintenanceSchedule(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service_date = models.DateField()
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.vehicle} - {self.service_date}"


class RepairLog(models.Model):

    CATEGORY_CHOICES = (
        ('ENGINE',        'Engine'),
        ('TRANSMISSION',  'Transmission'),
        ('BRAKES',        'Brakes'),
        ('TYRES',         'Tyres'),
        ('ELECTRICAL',    'Electrical'),
        ('BODY',          'Body & Panels'),
        ('SUSPENSION',    'Suspension'),
        ('FUEL_SYSTEM',   'Fuel System'),
        ('COOLING',       'Cooling System'),
        ('GENERAL',       'General Service'),
        ('OTHER',         'Other'),
    )

    PROGRESS_CHOICES = (
        ('PENDING',      'Pending'),
        ('IN_PROGRESS',  'In Progress'),
        ('COMPLETED',    'Completed'),
        ('ON_HOLD',      'On Hold'),
    )

    vehicle     = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='repair_logs')
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='GENERAL')
    issue       = models.TextField()
    mechanic    = models.CharField(max_length=100, blank=True, null=True)
    cost        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    progress    = models.CharField(max_length=20, choices=PROGRESS_CHOICES, default='PENDING')
    repaired_on = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle.number_plate} - {self.get_category_display()} ({self.get_progress_display()})"