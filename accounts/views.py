from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


# =====================
# LOGIN
# =====================
def login_view(request):

    if request.user.is_authenticated:
        return redirect_user(request.user)

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect_user(user)

        messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


# =====================
# REDIRECT LOGIC
# =====================
def redirect_user(user):
    if user.role == 'admin':
        return redirect('dashboard')
    return redirect('profile')


# =====================
# LOGOUT
# =====================
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# =====================
# PROFILE
# =====================
@login_required
def profile(request):
    return render(request, 'profile.html', {
        'user': request.user
    })