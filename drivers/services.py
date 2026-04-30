from .models import Driver
from payments.models import Payment
from django.db.models import Sum


def get_all_drivers():
    drivers = Driver.objects.select_related('user', 'assigned_vehicle').all()

    # 🔥 ADD REAL PERFORMANCE CALCULATION
    for d in drivers:
        payments = Payment.objects.filter(
            driver=d.user,
            status='SUCCESS'
        )

        d.total_collections = payments.aggregate(
            total=Sum('amount')
        )['total'] or 0

        d.total_trips = payments.count()

        # simple scoring logic (you can improve later)
        d.performance_score = float(d.total_trips)

    return drivers


def get_driver(driver_id):
    return Driver.objects.get(id=driver_id)


def update_performance(driver, score):
    driver.performance_score = score
    driver.save()
    return driver