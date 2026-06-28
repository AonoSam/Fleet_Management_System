from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .forms import UserCreateForm
from .services import get_all_users, create_user
from .permissions import admin_required, driver_required
from .models import User, UserSession

from payments.models import Payment
from loans.models import Loan
from drivers.models import Driver
from vehicles.models import Vehicle
from maintenance.models import MaintenanceSchedule, RepairLog
from django.contrib.sessions.models import Session


# ========================
# LANDING PAGE
# ========================
def landing(request):
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN':
            return redirect('admin_dashboard')
        return redirect('driver_dashboard')
    return render(request, 'landing.html')


# ========================
# AUTH
# ========================
from django.contrib.auth import authenticate, login, get_user_model

def login_view(request):
    raise Exception("LOGIN VIEW VERSION 1")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        User = get_user_model()

        print("\n========== LOGIN DEBUG ==========")
        print("Username entered:", username)
        print("Total users:", User.objects.count())

        user_obj = User.objects.filter(username=username).first()

        if user_obj:
            print("User exists: YES")
            print("Role:", user_obj.role)
            print("Active:", user_obj.is_active)
            print("Staff:", user_obj.is_staff)
            print("Superuser:", user_obj.is_superuser)
            print("Password correct:", user_obj.check_password(password))
            print("Password hash:", user_obj.password)
        else:
            print("User exists: NO")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        print("authenticate() returned:", user)
        print("================================\n")

        if user is not None:
            login(request, user)

            if user.role == "ADMIN":
                return redirect("admin_dashboard")

            return redirect("driver_dashboard")

        return render(request, "login.html", {
            "error": "Invalid credentials"
        })

    return render(request, "login.html")
def logout_view(request):
    # ✅ FIX: Mark UserSession as inactive BEFORE logout clears the user
    if request.user.is_authenticated:
        UserSession.objects.filter(
            user=request.user, is_active=True
        ).update(is_active=False, logout_time=timezone.now())

    logout(request)
    return redirect('login')


# ========================
# USER LIST
# ========================
@admin_required
def user_list(request):
    users = User.objects.all().order_by('role', 'username')

    # Build online set
    online_ids = set(
        UserSession.objects.filter(is_active=True).values_list('user_id', flat=True)
    )

    return render(request, 'user_list.html', {
        'users':      users,
        'online_ids': online_ids,
    })


# ========================
# CREATE USER
# ========================
@admin_required
def create_user_view(request):
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        create_user(form)
        messages.success(request, 'User created successfully.')
        return redirect('user_list')
    return render(request, 'create_user.html', {'form': form})


# ========================
# EDIT USER
# ========================
@admin_required
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        username     = request.POST.get('username', '').strip()
        role         = request.POST.get('role', user.role)
        phone_number = request.POST.get('phone_number', '').strip()
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        new_password = request.POST.get('new_password', '').strip()

        # Check username uniqueness (exclude self)
        if User.objects.filter(username=username).exclude(pk=pk).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'edit_user.html', {'u': user})

        user.username     = username
        user.role         = role
        user.phone_number = phone_number or None
        user.first_name   = first_name
        user.last_name    = last_name

        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, f'{user.username} updated successfully.')
        return redirect('user_list')

    return render(request, 'edit_user.html', {'u': user})


# ========================
# DELETE USER
# ========================
@admin_required
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')

    if request.method == 'POST':
        # Force logout first
        UserSession.objects.filter(
            user=user, is_active=True
        ).update(is_active=False, logout_time=timezone.now())

        all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in all_sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(user.pk):
                session.delete()

        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been permanently deleted.')
        return redirect('user_list')

    return render(request, 'delete_user.html', {'u': user})


# ========================
# ACTIVE USERS / SESSIONS
# ========================
@admin_required
def active_users(request):
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    since_24h   = timezone.now() - timedelta(hours=24)

    active_sessions = UserSession.objects.filter(
        is_active=True
    ).select_related('user').order_by('-login_time')

    recent_sessions = UserSession.objects.filter(
        login_time__gte=since_24h
    ).select_related('user').order_by('-login_time')

    all_users = User.objects.all().order_by('role', 'username')

    online_user_ids = set(
        active_sessions.values_list('user_id', flat=True)
    )

    total_users    = all_users.count()
    blocked_users  = all_users.filter(is_active=False).count()
    active_count   = active_sessions.count()
    sessions_today = UserSession.objects.filter(
        login_time__gte=today_start
    ).count()

    return render(request, 'active_users.html', {
        'active_sessions':  active_sessions,
        'recent_sessions':  recent_sessions,
        'all_users':        all_users,
        'online_user_ids':  online_user_ids,
        'active_count':     active_count,
        'total_users':      total_users,
        'blocked_users':    blocked_users,
        'sessions_today':   sessions_today,
    })


@admin_required
def force_logout_user(request, pk):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=pk)

        UserSession.objects.filter(
            user=target_user, is_active=True
        ).update(is_active=False, logout_time=timezone.now())

        all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in all_sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(target_user.pk):
                session.delete()

    return redirect('active_users')


@admin_required
def block_user(request, pk):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=pk)
        if target_user != request.user:
            target_user.is_active = False
            target_user.save()

            UserSession.objects.filter(
                user=target_user, is_active=True
            ).update(is_active=False, logout_time=timezone.now())

            all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
            for session in all_sessions:
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(target_user.pk):
                    session.delete()

    return redirect('active_users')


@admin_required
def unblock_user(request, pk):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=pk)
        target_user.is_active = True
        target_user.save()
    return redirect('active_users')


# ========================
# ADMIN DASHBOARD
# ========================
@admin_required
def admin_dashboard(request):
    today = timezone.now().date()

    total_vehicles             = Vehicle.objects.count()
    active_vehicles            = Vehicle.objects.filter(status='ACTIVE').count()
    under_maintenance_vehicles = Vehicle.objects.filter(status='MAINTENANCE').count()
    total_drivers              = User.objects.filter(role='DRIVER').count()

    payments          = Payment.objects.filter(status='SUCCESS')
    total_collections = payments.aggregate(total=Sum('amount'))['total'] or 0
    monthly_collections = payments.filter(
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0
    recent_payments = Payment.objects.order_by('-created_at')[:6]

    loans             = Loan.objects.exclude(status='REJECTED')
    active_loans      = loans.filter(status='ACTIVE').count()
    pending_loans     = loans.filter(status='PENDING').count()
    total_loan_amount = loans.aggregate(total=Sum('amount'))['total'] or 0

    overdue_schedules = MaintenanceSchedule.objects.filter(
        completed=False, service_date__lt=today
    ).count()
    upcoming_schedules = MaintenanceSchedule.objects.filter(
        completed=False, service_date__gte=today
    ).order_by('service_date')[:5]

    repairs_in_progress = RepairLog.objects.filter(progress='IN_PROGRESS').count()
    recent_repairs      = RepairLog.objects.select_related('vehicle').order_by('-created_at')[:5]

    return render(request, 'admin_dashboard.html', {
        'total_vehicles':             total_vehicles,
        'active_vehicles':            active_vehicles,
        'under_maintenance_vehicles': under_maintenance_vehicles,
        'total_drivers':              total_drivers,
        'total_collections':          total_collections,
        'monthly_collections':        monthly_collections,
        'recent_payments':            recent_payments,
        'active_loans':               active_loans,
        'pending_loans':              pending_loans,
        'total_loan_amount':          total_loan_amount,
        'overdue_schedules':          overdue_schedules,
        'upcoming_schedules':         upcoming_schedules,
        'repairs_in_progress':        repairs_in_progress,
        'recent_repairs':             recent_repairs,
        'today':                      today,
    })


# ========================
# DRIVER DASHBOARD
# ========================
@driver_required
def driver_dashboard(request):
    today   = timezone.now().date()
    driver  = Driver.objects.filter(user=request.user).first()
    vehicle = Vehicle.objects.filter(assigned_driver=request.user).first()

    payments            = Payment.objects.filter(driver=request.user)
    total_collections   = payments.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total'] or 0
    total_trips         = payments.filter(status='SUCCESS').count()
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
        overdue_maintenance  = [s for s in schedules if s.service_date < today]

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