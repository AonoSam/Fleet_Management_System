from django.shortcuts import render
from accounts.permissions import admin_required
from .services import (
    get_dashboard_stats,
    get_cost_report,
    get_driver_performance_report
)


# ----------------------
# DASHBOARD
# ----------------------
@admin_required
def dashboard(request):
    stats = get_dashboard_stats()
    return render(request, 'dashboard.html', stats)


# ----------------------
# COST REPORT
# ----------------------
@admin_required
def cost_report(request):
    costs = get_cost_report()
    return render(request, 'cost_report.html', {
        'costs': costs
    })


# ----------------------
# DRIVER PERFORMANCE
# ----------------------
@admin_required
def performance_report(request):
    report = get_driver_performance_report()
    return render(request, 'performance_report.html', {
        'report': report
    })