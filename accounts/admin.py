"""Django Admin registration for CustomUser."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration displaying role and contact information."""

    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "contact_number")
    fieldsets = UserAdmin.fieldsets + (
        ("ToolUp Profile", {"fields": ("role", "contact_number")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("ToolUp Profile", {"fields": ("email", "first_name", "last_name", "role", "contact_number")}),
    )
