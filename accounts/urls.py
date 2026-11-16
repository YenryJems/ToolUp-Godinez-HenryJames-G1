"""URL patterns for the accounts application."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardRedirectView.as_view(), name="dashboard"),
    path("dashboard/client/", views.ClientDashboardView.as_view(), name="client_dashboard"),
    path(
        "dashboard/technician/",
        views.TechnicianDashboardView.as_view(),
        name="technician_dashboard",
    ),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path(
        "dashboard/admin/users/<int:pk>/toggle-active/",
        views.AdminToggleUserActiveView.as_view(),
        name="admin_toggle_user",
    ),
    path("profile/", views.ProfileDetailView.as_view(), name="profile"),
    path("profile/<int:pk>/", views.ProfileDetailView.as_view(), name="profile_by_id"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path(
        "profile/<int:pk>/edit/",
        views.ProfileUpdateView.as_view(),
        name="profile_edit_by_id",
    ),
]
