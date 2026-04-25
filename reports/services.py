from vehicles.models import Vehicle
from drivers.models import Driver
from maintainance.models import MaintenanceSchedule, RepairLog
from payments.models import Payment
from django.db.models import Sum


# =====================
# DASHBOARD STATS
# =====================
def get_dashboard_data():

    total_vehicles = Vehicle.objects.count()
    total_drivers = Driver.objects.count()

    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0

    total_maintenance_cost = RepairLog.objects.aggregate(
        total=Sum('cost')
    )['total'] or 0

    return {
        "total_vehicles": total_vehicles,
        "total_drivers": total_drivers,
        "total_payments": total_payments,
        "total_maintenance_cost": total_maintenance_cost,
    }


# =====================
# COST REPORT
# =====================
def get_cost_report():
    repairs = RepairLog.objects.all().order_by('-repair_date')
    return repairs


# =====================
# PERFORMANCE REPORT
# =====================
def get_driver_performance():
    drivers = Driver.objects.all().order_by('-performance_score')
    return drivers