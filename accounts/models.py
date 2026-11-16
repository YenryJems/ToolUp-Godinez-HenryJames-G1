"""Custom user identity and role models for ToolUp."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Platform user supporting Client, Technician, and Admin roles."""

    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client (Homeowner)"
        TECHNICIAN = "TECHNICIAN", "Technician (Handyman)"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField("email address", unique=True)
    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    contact_number = models.CharField(max_length=20, blank=True, default="")

    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["username"]

    def save(self, *args, **kwargs) -> None:
        """Ensure Django superusers always carry the ADMIN platform role."""
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_client(self) -> bool:
        """Return True if the user holds the Client role."""
        return self.role == self.Role.CLIENT

    @property
    def is_technician(self) -> bool:
        """Return True if the user holds the Technician role."""
        return self.role == self.Role.TECHNICIAN

    @property
    def is_admin_role(self) -> bool:
        """Return True if the user holds the Admin role or is a superuser."""
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self) -> str:
        full_name = self.get_full_name().strip()
        return f"{full_name} ({self.username})" if full_name else self.username
