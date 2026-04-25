from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm


# =========================
# REGISTER VIEW (FIXED)
# =========================
def register_view(request):
    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect('login')
        else:
            # 🔥 DEBUG: show errors in terminal
            print("REGISTER ERRORS:", form.errors)

    return render(request, 'register.html', {'form': form})


# =========================
# LOGIN VIEW (FIXED)
# =========================
def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('profile')
        else:
            error = "Invalid username or password"

    return render(request, 'login.html', {'error': error})


# =========================
# LOGOUT VIEW
# =========================
def logout_view(request):
    logout(request)
    return redirect('login')


# =========================
# PROFILE VIEW
# =========================
@login_required
def profile_view(request):
    return render(request, 'profile.html')


# =========================
# DASHBOARD (ROLE BASED)
# =========================
@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return render(request, 'profile.html', {'role': 'admin'})
    else:
        return render(request, 'profile.html', {'role': 'driver'})