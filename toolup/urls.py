"""Root URL configuration for ToolUp."""

from django.contrib import admin
from django.urls import include, path

from accounts.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
]
