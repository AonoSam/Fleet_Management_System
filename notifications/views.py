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
# MARK SINGLE AS READ
# — stays on current page, or alerts page if direct visit
# -------------------------
def mark_read(request, pk):
    if request.method == "POST":
        mark_as_read(pk, request.user)
        # If called via fetch (AJAX), return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        # If submitted from the alerts page, stay on alerts
        referer = request.META.get('HTTP_REFERER', '')
        if 'notifications' in referer or 'alerts' in referer:
            return redirect('alerts')
        # Otherwise go back to where the user was
        return redirect(referer or 'alerts')
    return redirect('alerts')


# -------------------------
# MARK ALL AS READ (CLEAR ALL)
# — always returns JSON so the dropdown stays open
# -------------------------
def mark_all_read(request):
    if request.method == "POST":
        mark_all_as_read(request.user)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)