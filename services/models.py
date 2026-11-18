"""Service category models for ToolUp."""

from django.db import models


class ServiceCategory(models.Model):
    """Trade category offered on ToolUp (e.g., Plumbing, Electrical, IT Troubleshooting)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default="bi-tools")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "service_categories"
        ordering = ["id"]
        verbose_name_plural = "service categories"

    def __str__(self) -> str:
        return self.name
