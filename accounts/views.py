from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from django.utils import timezone

from .forms import UserCreateForm
from .services import get_all_users, create_user
from .permissions import admin_required, driver_required
from .models import User

from payments.models import Payment
from loans.models import Loan
from drivers.models import Driver
from vehicles.models import Vehicle
from maintenance.models import MaintenanceSchedule, RepairLog


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.role == 'ADMIN':
                return redirect('admin_dashboard')
            return redirect('driver_dashboard')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@admin_required
def user_list(request):
    users = get_all_users()
    return render(request, 'user_list.html', {'users': users})


@admin_required
def create_user_view(request):
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        create_user(form)
        return redirect('user_list')
    return render(request, 'create_user.html', {'form': form})


@admin_required
def admin_dashboard(request):
    today = timezone.now().date()

    # ── Fleet ────────────────────────────────────────────────────
    total_vehicles  = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status='ACTIVE').count()
    under_maintenance_vehicles = Vehicle.objects.filter(status='MAINTENANCE').count()

    # ── Drivers ──────────────────────────────────────────────────
    total_drivers = User.objects.filter(role='DRIVER').count()

    # ── Payments ─────────────────────────────────────────────────
    payments = Payment.objects.filter(status='SUCCESS')

    total_collections = payments.aggregate(
        total=Sum('amount')
    )['total'] or 0

    monthly_collections = payments.filter(
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_payments = Payment.objects.order_by('-created_at')[:6]

    # ── Loans ─────────────────────────────────────────────────────
    loans = Loan.objects.exclude(status='REJECTED')
    active_loans  = loans.filter(status='ACTIVE').count()
    pending_loans = loans.filter(status='PENDING').count()

    total_loan_amount = loans.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # ── Maintenance ───────────────────────────────────────────────
    overdue_schedules = MaintenanceSchedule.objects.filter(
        completed=False,
        service_date__lt=today
    ).count()

    upcoming_schedules = MaintenanceSchedule.objects.filter(
        completed=False,
        service_date__gte=today
    ).order_by('service_date')[:5]

    # ── Repairs ───────────────────────────────────────────────────
    repairs_in_progress = RepairLog.objects.filter(
        progress='IN_PROGRESS'
    ).count()

    recent_repairs = RepairLog.objects.select_related('vehicle').order_by('-created_at')[:5]

    return render(request, 'admin_dashboard.html', {
        # fleet
        'total_vehicles':             total_vehicles,
        'active_vehicles':            active_vehicles,
        'under_maintenance_vehicles': under_maintenance_vehicles,
        # drivers
        'total_drivers':              total_drivers,
        # payments
        'total_collections':          total_collections,
        'monthly_collections':        monthly_collections,
        'recent_payments':            recent_payments,
        # loans
        'active_loans':               active_loans,
        'pending_loans':              pending_loans,
        'total_loan_amount':          total_loan_amount,
        # maintenance
        'overdue_schedules':          overdue_schedules,
        'upcoming_schedules':         upcoming_schedules,
        'repairs_in_progress':        repairs_in_progress,
        'recent_repairs':             recent_repairs,
        'today':                      today,
    })


@driver_required
def driver_dashboard(request):
    today = timezone.now().date()

    driver  = Driver.objects.filter(user=request.user).first()
    vehicle = Vehicle.objects.filter(assigned_driver=request.user).first()

    payments = Payment.objects.filter(driver=request.user)

    total_collections = payments.filter(status='SUCCESS').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_trips = payments.filter(status='SUCCESS').count()

    monthly_collections = payments.filter(
        status='SUCCESS',
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_payments = payments.order_by('-created_at')[:5]

    loans        = Loan.objects.filter(driver=request.user)
    active_loans = loans.filter(status='ACTIVE')
    loan_balance = sum(loan.balance() for loan in active_loans)
    active_loan  = active_loans.first()

    upcoming_maintenance = []
    overdue_maintenance  = []

    if vehicle:
        schedules = MaintenanceSchedule.objects.filter(
            vehicle=vehicle, completed=False
        ).order_by('service_date')
        upcoming_maintenance = [s for s in schedules if s.service_date >= today][:3]
        overdue_maintenance  = [s for s in schedules if s.service_date <  today]

    return render(request, 'driver_dashboard.html', {
        'driver':               driver,
        'vehicle':              vehicle,
        'total_collections':    total_collections,
        'monthly_collections':  monthly_collections,
        'total_trips':          total_trips,
        'recent_payments':      recent_payments,
        'active_loan':          active_loan,
        'loan_balance':         loan_balance,
        'active_loans_count':   active_loans.count(),
        'upcoming_maintenance': upcoming_maintenance,
        'overdue_maintenance':  overdue_maintenance,
        'overdue_count':        len(overdue_maintenance),
    })