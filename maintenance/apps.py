"""
maintenance/apps.py

── THE CORE FIX FOR THIS INCIDENT ──

check_maintenance_alerts was a correctly-written management
command that NOTHING ever called automatically. Django signals
only fire on database writes — there is no signal for "a day
has passed," so the 2-day-before and due-today alerts could
only ever fire if a human remembered to run:

    python manage.py check_maintenance_alerts

every single day. That's the entire root cause of "alerts are
not sending automatically."

This file now starts an APScheduler background job the moment
the Django app boots, which calls that same management command
once every 24 hours automatically, for as long as the server
process is running. No external cron, no Task Scheduler entry,
no manual intervention required.

Requires: pip install apscheduler
"""

from django.apps import AppConfig
import os


class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maintenance'

    def ready(self):
        import maintenance.signals  # noqa — existing signal registration, unchanged

        # ── Guard against double-start ──
        # Django's runserver starts TWO processes in dev mode (the
        # reloader + the actual worker). Without this check, the
        # scheduler would start twice, doubling every alert. The
        # RUN_MAIN env var is only set in the actual worker process,
        # never in the reloader's watcher process.
        if os.environ.get('RUN_MAIN') != 'true' and not os.environ.get('DJANGO_SETTINGS_MODULE_PROD_RUN'):
            # In dev with the autoreloader, only proceed in the real
            # worker process. In production (gunicorn/waitress, no
            # reloader), RUN_MAIN is never set at all, so we still
            # need to allow startup there — handled below.
            import sys
            if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
                return

        self._start_scheduler()

    def _start_scheduler(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            import logging
            logging.getLogger(__name__).warning(
                "APScheduler is not installed — maintenance alerts will "
                "NOT run automatically. Install it with: "
                "pip install apscheduler"
            )
            return

        def run_alert_check():
            from django.core.management import call_command
            try:
                call_command('check_maintenance_alerts')
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    "check_maintenance_alerts failed during scheduled run"
                )

        scheduler = BackgroundScheduler(timezone="Africa/Nairobi")

        # Runs once a day at 07:00 Nairobi time — adjust as needed.
        # Using a cron trigger (not interval) so it fires at a fixed
        # wall-clock time every day rather than "every 24 hours from
        # whenever the server happened to start."
        scheduler.add_job(
            run_alert_check,
            trigger=CronTrigger(hour=7, minute=0),
            id='check_maintenance_alerts_daily',
            replace_existing=True,
            misfire_grace_time=3600,  # if the server was down at 7am, still run within 1hr of starting
        )

        scheduler.start()

        # Also run once immediately on startup, so you don't have to
        # wait until 7am to see it working / to catch up on any
        # alerts missed while the server was off.
        run_alert_check()