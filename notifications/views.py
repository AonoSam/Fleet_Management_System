from django.shortcuts import render
from django.http import JsonResponse
from accounts.permissions import admin_required, driver_required
from .services import (
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read
)


def alerts(request):
    notifications = get_user_notifications(request.user)
    return render(request, 'alerts.html', {
        'notifications': notifications
    })


# 🔴 UNREAD COUNT (FOR BELL)
def unread_count(request):
    count = get_unread_count(request.user)
    return JsonResponse({'unread': count})


# ✔ MARK SINGLE AS READ
def mark_read(request, pk):
    mark_as_read(pk, request.user)
    return JsonResponse({'status': 'ok'})


# ✔ MARK ALL AS READ
def mark_all_read(request):
    mark_all_as_read(request.user)
    return JsonResponse({'status': 'ok'})