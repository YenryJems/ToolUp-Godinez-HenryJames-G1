"""Django Admin registration for Booking."""

from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for service bookings."""

    list_display = ("id", "client", "technician", "service_date", "time_slot", "status", "created_at")
    list_filter = ("status", "service_date", "time_slot")
    search_fields = ("client__username", "technician__user__username", "service_address", "issue_description")
