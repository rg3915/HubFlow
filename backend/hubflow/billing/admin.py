from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'hourly_rate', 'invoice_number', 'issue_date', 'payment_date', 'status')
    list_filter = ('status', 'sprint__project__client')
