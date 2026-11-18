"""App configuration for technicians."""

from django.apps import AppConfig


class TechniciansConfig(AppConfig):
    """Configuration class for the technicians application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "technicians"
