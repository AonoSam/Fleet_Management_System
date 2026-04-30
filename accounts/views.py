from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import UserCreateForm
from .services import get_all_users, create_user
from .permissions import admin_required


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


def driver_dashboard(request):
    return render(request, 'driver_dashboard.html')