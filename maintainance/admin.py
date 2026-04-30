from django.contrib import admin
from .models import MaintenanceSchedule, RepairLog


admin.site.register(MaintenanceSchedule)
admin.site.register(RepairLog)