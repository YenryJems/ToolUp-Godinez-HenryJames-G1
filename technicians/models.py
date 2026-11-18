"""Technician profile and verification document models for ToolUp."""

from decimal import Decimal

from django.conf import settings
from django.db import models

from config.constants import CEBU_CITY_BARANGAYS


class TechnicianProfile(models.Model):
    """Cebu City handyman trade profile, service options, and admin verification state."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technician_profile",
    )
    category = models.ForeignKey(
        "services.ServiceCategory",
        on_delete=models.PROTECT,
        related_name="technicians",
    )
    barangay = models.CharField(max_length=100, choices=CEBU_CITY_BARANGAYS)
    bio = models.TextField()
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("450.00"),
    )
    is_accepting_bookings = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "technician_profiles"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hourly_rate__gte=0),
                name="technician_hourly_rate_gte_0",
            ),
        ]

    def __str__(self) -> str:
        full_name = self.user.get_full_name().strip() or self.user.username
        return f"{full_name} ({self.category.name} - {self.barangay})"


class VerificationDocument(models.Model):
    """Credential uploaded by a technician for admin approval."""

    class DocumentType(models.TextChoices):
        TRADE_LICENSE = "TRADE_LICENSE", "Trade License / TESDA NC"
        BARANGAY_CLEARANCE = "BARANGAY_CLEARANCE", "Barangay Clearance"
        GOVERNMENT_ID = "GOVERNMENT_ID", "Government ID"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    technician = models.ForeignKey(
        TechnicianProfile,
        on_delete=models.CASCADE,
        related_name="verification_documents",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file_path = models.FileField(upload_to="verification_docs/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    rejection_reason = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_documents"
        ordering = ["-submitted_at", "-id"]

    def __str__(self) -> str:
        return f"{self.technician} - {self.document_type} ({self.status})"
