from django.contrib import admin
from .models import MaintenanceSchedule, RepairLog


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_type', 'due_date', 'is_completed')
    list_filter = ('is_completed', 'due_date')


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'issue', 'cost', 'repair_date')
    list_filter = ('repair_date',)