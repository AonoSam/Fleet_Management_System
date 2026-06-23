"""
Run this once a day (via cron, Task Scheduler, or a hosting
platform's scheduled job) to send maintenance alerts:

    python manage.py check_maintenance_alerts

It sends:
- An "upcoming" alert 2 days BEFORE the service_date
- A "due today" alert ON the service_date

Both go to the assigned driver (if any) and to every admin.
Each alert is only sent once per schedule (tracked via the
upcoming_alert_sent / due_alert_sent boolean fields).
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from maintenance.models import MaintenanceSchedule
from notifications.models import Notification
from accounts.models import User


class Command(BaseCommand):
    help = "Send maintenance alerts: 2 days before and on the due date."

    def handle(self, *args, **options):
        today = timezone.now().date()
        two_days_from_now = today + timedelta(days=2)

        upcoming_count = self.send_upcoming_alerts(two_days_from_now)
        due_count = self.send_due_alerts(today)

        self.stdout.write(self.style.SUCCESS(
            f"Sent {upcoming_count} upcoming alert(s) and {due_count} due-today alert(s)."
        ))

    def notify(self, user, message, n_type='MAINTENANCE'):
        if user:
            Notification.objects.create(
                user=user, message=message, notification_type=n_type
            )

    def notify_admins(self, message):
        for admin in User.objects.filter(role='ADMIN'):
            self.notify(admin, message)

    def send_upcoming_alerts(self, target_date):
        schedules = MaintenanceSchedule.objects.filter(
            service_date=target_date,
            completed=False,
            upcoming_alert_sent=False,
        ).select_related('vehicle', 'vehicle__assigned_driver')

        count = 0
        for s in schedules:
            vehicle = s.vehicle
            driver = vehicle.assigned_driver

            msg = (
                f"Reminder: {vehicle.number_plate} is due for maintenance "
                f"in 2 days ({s.service_date}). {s.description}"
            )

            if driver:
                self.notify(driver, msg)
            self.notify_admins(msg)

            s.upcoming_alert_sent = True
            s.save(update_fields=['upcoming_alert_sent'])
            count += 1

        return count

    def send_due_alerts(self, target_date):
        schedules = MaintenanceSchedule.objects.filter(
            service_date=target_date,
            completed=False,
            due_alert_sent=False,
        ).select_related('vehicle', 'vehicle__assigned_driver')

        count = 0
        for s in schedules:
            vehicle = s.vehicle
            driver = vehicle.assigned_driver

            msg = (
                f"Maintenance due TODAY for {vehicle.number_plate}: {s.description}"
            )

            if driver:
                self.notify(driver, msg)
            self.notify_admins(msg)

            s.due_alert_sent = True
            s.save(update_fields=['due_alert_sent'])
            count += 1

        return count