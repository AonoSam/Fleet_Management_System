from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'license_number',
        'phone',
        'assigned_vehicle',
        'performance_score',
        'total_trips',
        'total_collections'
    )

    list_filter = ('performance_score',)
    search_fields = ('user__username', 'license_number')