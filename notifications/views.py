from django.shortcuts import render, redirect
from django.http import JsonResponse
from accounts.permissions import admin_required, driver_required
from .services import (
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read
)


# -------------------------
# NOTIFICATION PAGE
# -------------------------
def alerts(request):
    notifications = get_user_notifications(request.user)

    return render(request, 'alerts.html', {
        'notifications': notifications
    })


# -------------------------
# UNREAD COUNT (BELL AJAX)
# -------------------------
def unread_count(request):
    count = get_unread_count(request.user)
    return JsonResponse({'unread': count})


# -------------------------
# MARK SINGLE AS READ (AJAX)
# -------------------------
def mark_read(request, pk):
    if request.method == "POST":
        mark_as_read(pk, request.user)
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'invalid'}, status=400)


# -------------------------
# MARK ALL AS READ (FORM SUBMIT)
# -------------------------
def mark_all_read(request):
    if request.method == "POST":
        mark_all_as_read(request.user)

    return redirect('alerts')