from django.db import models
from django.utils import timezone
from datetime import timedelta
from vehicles.models import Vehicle


class MaintenanceSchedule(models.Model):

    ALERT_NONE     = 'NONE'
    ALERT_UPCOMING = 'UPCOMING'
    ALERT_DUE      = 'DUE'

    vehicle      = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service_date = models.DateField()
    description  = models.TextField()
    completed    = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    # ── Auto-generated recurring schedules ──
    auto_generated = models.BooleanField(default=False)

    # ── Alert tracking (prevents duplicate notifications) ──
    upcoming_alert_sent = models.BooleanField(default=False)
    due_alert_sent      = models.BooleanField(default=False)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.vehicle} - {self.service_date}"

    @property
    def is_overdue(self):
        return not self.completed and self.service_date < timezone.now().date()

    @property
    def days_until(self):
        return (self.service_date - timezone.now().date()).days


class VehicleMaintenancePlan(models.Model):
    """
    One plan per vehicle. Defines how often maintenance should
    recur (in days). Used to auto-generate the next
    MaintenanceSchedule once the current one is completed.
    """

    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='maintenance_plan'
    )

    interval_days = models.PositiveIntegerField(
        default=90,
        help_text="Number of days between scheduled maintenance services."
    )

    default_description = models.CharField(
        max_length=255,
        default="Routine scheduled maintenance",
        blank=True
    )

    is_active = models.BooleanField(default=True)

    last_scheduled_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle.number_plate} — every {self.interval_days} days"

    def next_due_date(self, from_date=None):
        base = from_date or self.last_scheduled_date or timezone.now().date()

        # Defensive: handle case where base might be an empty
        # string or otherwise not a proper date object
        if not base or isinstance(base, str):
            base = timezone.now().date()

        return base + timedelta(days=self.interval_days)

    def generate_next_schedule(self):
        """
        Creates the next MaintenanceSchedule for this vehicle
        based on the interval, if one doesn't already exist
        for that date.
        """
        next_date = self.next_due_date()

        exists = MaintenanceSchedule.objects.filter(
            vehicle=self.vehicle,
            service_date=next_date,
            completed=False
        ).exists()

        if not exists:
            schedule = MaintenanceSchedule.objects.create(
                vehicle=self.vehicle,
                service_date=next_date,
                description=self.default_description,
                auto_generated=True,
            )
            self.last_scheduled_date = next_date
            self.save(update_fields=['last_scheduled_date'])
            return schedule

        return None


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