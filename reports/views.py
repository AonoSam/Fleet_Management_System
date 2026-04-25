from django.shortcuts import render
from .services import (
    get_dashboard_data,
    get_cost_report,
    get_driver_performance
)


# =====================
# DASHBOARD
# =====================
def dashboard(request):

    data = get_dashboard_data()

    return render(request, 'dashboard.html', data)


# =====================
# COST REPORT
# =====================
def cost_report(request):

    repairs = get_cost_report()

    return render(request, 'cost_report.html', {
        'repairs': repairs
    })


# =====================
# PERFORMANCE REPORT
# =====================
def performance_report(request):

    drivers = get_driver_performance()

    return render(request, 'performance_report.html', {
        'drivers': drivers
    })