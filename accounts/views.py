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
from maintenance.models import MaintenanceSchedule


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


def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@driver_required
def driver_dashboard(request):
    today = timezone.now().date()

    # ── Driver profile ──────────────────────────────────────────
    driver = Driver.objects.filter(user=request.user).first()

    # ── Assigned vehicle (Vehicle owns the FK) ──────────────────
    vehicle = Vehicle.objects.filter(assigned_driver=request.user).first()

    # ── Payments ────────────────────────────────────────────────
    payments = Payment.objects.filter(driver=request.user)

    total_collections = payments.filter(status='SUCCESS').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_trips = payments.filter(status='SUCCESS').count()

    # Collections this month only
    monthly_collections = payments.filter(
        status='SUCCESS',
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_payments = payments.order_by('-created_at')[:5]

    # ── Loans ────────────────────────────────────────────────────
    loans = Loan.objects.filter(driver=request.user)
    active_loans = loans.filter(status='ACTIVE')

    # Total outstanding balance across all active loans
    loan_balance = sum(loan.balance() for loan in active_loans)

    # Most recent active loan for detail display
    active_loan = active_loans.first()

    # ── Maintenance (for this driver's vehicle) ──────────────────
    upcoming_maintenance = []
    overdue_maintenance  = []

    if vehicle:
        schedules = MaintenanceSchedule.objects.filter(
            vehicle=vehicle,
            completed=False
        ).order_by('service_date')

        upcoming_maintenance = [s for s in schedules if s.service_date >= today][:3]
        overdue_maintenance  = [s for s in schedules if s.service_date <  today]

    return render(request, 'driver_dashboard.html', {
        # profile
        'driver':               driver,
        'vehicle':              vehicle,
        # payments
        'total_collections':    total_collections,
        'monthly_collections':  monthly_collections,
        'total_trips':          total_trips,
        'recent_payments':      recent_payments,
        # loans
        'active_loan':          active_loan,
        'loan_balance':         loan_balance,
        'active_loans_count':   active_loans.count(),
        # maintenance
        'upcoming_maintenance': upcoming_maintenance,
        'overdue_maintenance':  overdue_maintenance,
        'overdue_count':        len(overdue_maintenance),
    })