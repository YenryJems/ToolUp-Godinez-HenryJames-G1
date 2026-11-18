"""Django Admin registration for Review."""

from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for booking reviews."""

    list_display = ("id", "booking", "client", "technician", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("client__username", "technician__user__username", "comment")
