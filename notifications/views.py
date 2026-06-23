from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from accounts.permissions import admin_required, driver_required
from .models import Notification
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
    unread        = notifications.filter(is_read=False).count()
    total         = notifications.count()
    return render(request, 'alerts.html', {
        'notifications': notifications,
        'unread_count':  unread,
        'total_count':   total,
    })


# -------------------------
# UNREAD COUNT (BELL AJAX)
# -------------------------
def unread_count(request):
    count = get_unread_count(request.user)
    return JsonResponse({'unread': count})


# -------------------------
# MARK SINGLE AS READ
# -------------------------
def mark_read(request, pk):
    if request.method == 'POST':
        mark_as_read(pk, request.user)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        referer = request.META.get('HTTP_REFERER', '')
        if 'notifications' in referer or 'alerts' in referer:
            return redirect('alerts')
        return redirect(referer or 'alerts')
    return redirect('alerts')


# -------------------------
# MARK ALL AS READ
# -------------------------
def mark_all_read(request):
    if request.method == 'POST':
        mark_all_as_read(request.user)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


# -------------------------
# DELETE SINGLE NOTIFICATION
# -------------------------
@require_POST
def delete_notification(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).delete()
    return redirect('alerts')


# -------------------------
# DELETE SELECTED NOTIFICATIONS
# -------------------------
@require_POST
def delete_selected(request):
    ids = request.POST.getlist('selected_ids')
    if ids:
        Notification.objects.filter(
            pk__in=ids, user=request.user
        ).delete()
    return redirect('alerts')


# -------------------------
# DELETE ALL NOTIFICATIONS
# -------------------------
@require_POST
def delete_all(request):
    Notification.objects.filter(user=request.user).delete()
    return redirect('alerts')