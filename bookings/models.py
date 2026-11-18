"""Booking and scheduling models for ToolUp."""

from django.conf import settings
from django.db import models

from config.constants import TIME_SLOTS


class Booking(models.Model):
    """Scheduled service visit requested by a Client for a verified Technician."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_bookings",
    )
    technician = models.ForeignKey(
        "technicians.TechnicianProfile",
        on_delete=models.CASCADE,
        related_name="technician_bookings",
    )
    service_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOTS)
    service_address = models.TextField()
    issue_description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["technician", "service_date", "time_slot"],
                condition=models.Q(status__in=["PENDING", "ACCEPTED"]),
                name="unique_active_booking_slot",
            ),
        ]

    def __str__(self) -> str:
        return f"Booking #{self.pk} ({self.status}) - {self.service_date} {self.time_slot}"
