from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('driver', 'vehicle', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('driver__username', 'reference')