from django.shortcuts import render
from .services import get_user_notifications


def alerts_view(request):
    notifications = get_user_notifications(request.user)

    return render(request, 'alerts.html', {
        'notifications': notifications
    })