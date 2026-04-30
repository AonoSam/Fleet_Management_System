from payments.models import Payment
from drivers.models import Driver
from maintainance.models import RepairLog
from django.db.models import Sum


def get_dashboard_stats():
    total_payments = Payment.objects.filter(status='SUCCESS').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_repairs = RepairLog.objects.aggregate(
        total=Sum('cost')
    )['total'] or 0

    total_drivers = Driver.objects.count()

    return {
        "total_income": total_payments,
        "total_expenses": total_repairs,
        "net_profit": total_payments - total_repairs,
        "total_drivers": total_drivers,
    }


def get_cost_report():
    return RepairLog.objects.select_related('vehicle').all()


def get_driver_performance_report():
    drivers = Driver.objects.all()

    report = []

    for d in drivers:
        payments = Payment.objects.filter(driver=d.user, status='SUCCESS')

        total = payments.aggregate(total=Sum('amount'))['total'] or 0
        trips = payments.count()

        report.append({
            "driver": d,
            "total_collections": total,
            "trips": trips,
            "score": trips,
        })

    return report