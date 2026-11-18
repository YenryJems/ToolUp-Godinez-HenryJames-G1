"""Django Admin registration for TechnicianProfile and VerificationDocument."""

from django.contrib import admin

from .models import TechnicianProfile, VerificationDocument


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    """Admin configuration for technician profiles."""

    list_display = ("user", "category", "barangay", "hourly_rate", "is_accepting_bookings", "is_verified")
    list_filter = ("category", "barangay", "is_verified", "is_accepting_bookings")
    search_fields = ("user__username", "user__first_name", "user__last_name", "bio")


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for verification documents."""

    list_display = ("technician", "document_type", "status", "submitted_at")
    list_filter = ("document_type", "status")
    search_fields = ("technician__user__username", "rejection_reason")
