"""
maintenance/management/commands/check_maintenance_alerts.py

Run manually for testing:
    python manage.py check_maintenance_alerts

In production this runs automatically via the APScheduler job
registered in maintenance/apps.py.

── REDESIGNED RESPONSIBILITY ──
This command now does THREE things, in order:

1. MATERIALIZE upcoming schedules — for every active
   VehicleMaintenancePlan, compute next_due_date(). If that date
   is exactly 2 days from today AND no MaintenanceSchedule row
   exists yet for it, CREATE the row now and send the "upcoming"
   alert immediately (since the row is brand new, there's
   nothing to "wait" on — we just created it specifically
   because we're 2 days out).

2. SEND upcoming alerts for any OTHER schedule that already
   exists (e.g. manually created by an admin) and happens to
   land exactly 2 days out, in case it wasn't created by step 1.

3. SEND due-today alerts — unchanged from before.

This replaces the old design where the next MaintenanceSchedule
was created immediately upon marking the previous one complete.
Now the row simply does not exist in the database until 2 days
before it's due.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from maintenance.models import MaintenanceSchedule, VehicleMaintenancePlan
from notifications.models import Notification
from accounts.models import User


def get_local_today():
    """
    Returns today's date in the project's configured local
    timezone (Africa/Nairobi), not raw UTC. Single source of
    truth for "what day is it" across the maintenance app.
    """
    now_utc = timezone.now()
    now_local = timezone.localtime(now_utc)
    return now_local.date()


class Command(BaseCommand):
    help = "Materialize upcoming maintenance schedules and send 2-day/due-today alerts."

    def handle(self, *args, **options):
        today = get_local_today()
        two_days_from_now = today + timedelta(days=2)

        materialized_count = self.materialize_upcoming_schedules(two_days_from_now)
        upcoming_count = self.send_upcoming_alerts(two_days_from_now)
        due_count = self.send_due_alerts(today)

        self.stdout.write(self.style.SUCCESS(
            f"[{today}] Materialized {materialized_count} new schedule(s), "
            f"sent {upcoming_count} upcoming alert(s), "
            f"sent {due_count} due-today alert(s)."
        ))

    def notify(self, user, message, n_type='MAINTENANCE'):
        if user:
            Notification.objects.create(
                user=user, message=message, notification_type=n_type
            )

    def notify_admins(self, message):
        for admin in User.objects.filter(role='ADMIN'):
            self.notify(admin, message)

    # ------------------------------------------------------------
    # STEP 1: Materialize schedules that are now exactly 2 days out
    # ------------------------------------------------------------
    def materialize_upcoming_schedules(self, target_date):
        plans = VehicleMaintenancePlan.objects.filter(
            is_active=True
        ).select_related('vehicle', 'vehicle__assigned_driver')

        count = 0
        for plan in plans:
            next_date = plan.next_due_date()

            if next_date != target_date:
                continue  # not yet time to materialize this one

            # Avoid duplicating if a schedule already exists for
            # this vehicle around this date (e.g. admin manually
            # created one, or this command ran twice in a day)
            already_exists = MaintenanceSchedule.objects.filter(
                vehicle=plan.vehicle,
                service_date=next_date,
            ).exists()

            if already_exists:
                continue

            schedule = MaintenanceSchedule.objects.create(
                vehicle=plan.vehicle,
                service_date=next_date,
                description=plan.default_description,
                auto_generated=True,
            )

            # This schedule was JUST created specifically because
            # we're 2 days out — send the upcoming alert now and
            # mark it sent so step 2 doesn't send it again.
            vehicle = plan.vehicle
            driver = vehicle.assigned_driver

            msg = (
                f"Reminder: {vehicle.number_plate} is due for maintenance "
                f"in 2 days ({schedule.service_date}). {schedule.description}"
            )
            if driver:
                self.notify(driver, msg)
            self.notify_admins(msg)

            schedule.upcoming_alert_sent = True
            schedule.save(update_fields=['upcoming_alert_sent'])

            plan.last_scheduled_date = next_date
            plan.save(update_fields=['last_scheduled_date'])

            count += 1

        return count

    # ------------------------------------------------------------
    # STEP 2: Upcoming alerts for schedules NOT created by step 1
    # (e.g. manually created by an admin ahead of time)
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # STEP 3: Due-today alerts — unchanged
    # ------------------------------------------------------------
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