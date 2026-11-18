"""Root URL configuration for ToolUp."""

from django.contrib import admin
from django.urls import include, path

from accounts.views import (
    AdminVerificationQueueView,
    BookingCreateView,
    BookingDetailView,
    HomeView,
    ReviewCreateView,
    ServiceDirectoryView,
    TechnicianPublicProfileView,
    TechnicianServiceOptionsView,
    TechnicianVerificationUploadView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("directory/", ServiceDirectoryView.as_view(), name="directory"),
    path(
        "technicians/<int:pk>/",
        TechnicianPublicProfileView.as_view(),
        name="technician_detail",
    ),
    path(
        "technicians/profile/edit/",
        TechnicianServiceOptionsView.as_view(),
        name="technician_profile_edit",
    ),
    path(
        "technicians/verification/",
        TechnicianVerificationUploadView.as_view(),
        name="technician_verification",
    ),
    path(
        "dashboard/admin/verifications/",
        AdminVerificationQueueView.as_view(),
        name="admin_verification_queue",
    ),
    path(
        "bookings/create/<int:technician_id>/",
        BookingCreateView.as_view(),
        name="booking_create",
    ),
    path(
        "bookings/<int:pk>/",
        BookingDetailView.as_view(),
        name="booking_detail",
    ),
    path(
        "reviews/create/<int:booking_id>/",
        ReviewCreateView.as_view(),
        name="review_create",
    ),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
]
