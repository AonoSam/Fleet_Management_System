from django.shortcuts import redirect


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'ADMIN':
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper


def driver_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'DRIVER':
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper