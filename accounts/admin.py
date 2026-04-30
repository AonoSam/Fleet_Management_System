from django.contrib import admin
from .models import User, DriverProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'phone_number')
    list_filter = ('role',)


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'performance_score')