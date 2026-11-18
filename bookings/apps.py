"""App configuration for bookings."""

from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """Configuration class for the bookings application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bookings"
