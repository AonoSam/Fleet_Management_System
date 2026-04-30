from django.db import models
from vehicles.models import Vehicle


class MaintenanceSchedule(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service_date = models.DateField()
    description = models.TextField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vehicle} - {self.service_date}"


class RepairLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    issue = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    repaired_on = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle} - {self.issue}"