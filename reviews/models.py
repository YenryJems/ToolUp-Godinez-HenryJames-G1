"""Client review and rating models for ToolUp."""

from django.conf import settings
from django.db import models


class Review(models.Model):
    """Client rating (1-5) and feedback for a single completed booking."""

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="review",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_reviews",
    )
    technician = models.ForeignKey(
        "technicians.TechnicianProfile",
        on_delete=models.CASCADE,
        related_name="technician_reviews",
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_1_to_5",
            ),
        ]

    def __str__(self) -> str:
        return f"Review #{self.pk} ({self.rating}/5) for Booking #{self.booking_id}"
