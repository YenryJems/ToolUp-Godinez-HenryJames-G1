"""Views for ToolUp registration, authentication, role dashboards, and profiles."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from config.constants import CEBU_CITY_BARANGAY_NAMES

from .forms import CustomLoginForm, CustomUserRegistrationForm, UserProfileUpdateForm
from .mixins import AdminRequiredMixin, ClientRequiredMixin, TechnicianRequiredMixin
from .models import CustomUser


class HomeView(TemplateView):
    """Landing view routing logged-in users to their dashboard and guests to ToolUp home."""

    template_name = "accounts/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")
        return super().dispatch(request, *args, **kwargs)


class RegisterView(CreateView):
    """Register a new Client or Technician account using Django password hashing."""

    model = CustomUser
    form_class = CustomUserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Account created successfully! Please log in with your new credentials.",
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Registration failed. Please fix the highlighted fields below.",
        )
        return super().form_invalid(form)


class UserLoginView(LoginView):
    """Authenticate registered users and route them to their role-specific dashboard."""

    authentication_form = CustomLoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        messages.success(self.request, f"Welcome back, {user.first_name or user.username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Invalid username or password. Please check your credentials and try again.",
        )
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    """Terminate the user's session and redirect to the login page."""

    next_page = reverse_lazy("accounts:login")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been logged out successfully.")
        return response


class DashboardRedirectView(LoginRequiredMixin, View):
    """Dispatch authenticated users strictly to their role-specific dashboard."""

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_admin_role:
            return redirect("accounts:admin_dashboard")
        if user.is_technician:
            return redirect("accounts:technician_dashboard")
        return redirect("accounts:client_dashboard")


class ClientDashboardView(ClientRequiredMixin, TemplateView):
    """Role-specific dashboard for Cebu City Client (Homeowner) accounts."""

    template_name = "accounts/client_dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["barangay_count"] = len(CEBU_CITY_BARANGAY_NAMES)
        return context


class TechnicianDashboardView(TechnicianRequiredMixin, TemplateView):
    """Role-specific dashboard for local Technician (Handyman) accounts."""

    template_name = "accounts/technician_dashboard.html"


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Role-specific dashboard for Platform Admin accounts and user access management."""

    template_name = "accounts/admin_dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        users_qs = CustomUser.objects.order_by("-date_joined", "username")
        context["users_list"] = users_qs
        context["total_users"] = users_qs.count()
        context["client_count"] = users_qs.filter(role=CustomUser.Role.CLIENT).count()
        context["technician_count"] = users_qs.filter(role=CustomUser.Role.TECHNICIAN).count()
        context["active_users_count"] = users_qs.filter(is_active=True).count()
        return context


class AdminToggleUserActiveView(AdminRequiredMixin, View):
    """Allow Admins to activate or deactivate non-self user accounts."""

    http_method_names = ["post"]

    def post(self, request, pk: int, *args, **kwargs):
        target_user = get_object_or_404(CustomUser, pk=pk)
        if target_user.pk == request.user.pk:
            messages.error(request, "You cannot deactivate your own admin account.")
            return redirect("accounts:admin_dashboard")

        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active"])
        state_label = "activated" if target_user.is_active else "deactivated"
        messages.success(request, f"Account '{target_user.username}' has been {state_label}.")
        return redirect("accounts:admin_dashboard")


class OwnProfileMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensure users can only view and edit their own account profile."""

    def test_func(self) -> bool:
        target_pk = self.kwargs.get("pk")
        if target_pk is None:
            return True
        return int(target_pk) == self.request.user.pk

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You can only view and edit your own profile.")
        return super().handle_no_permission()

    def get_object(self, queryset=None) -> CustomUser:
        return self.request.user


class ProfileDetailView(OwnProfileMixin, DetailView):
    """Display the currently logged-in user's account profile."""

    model = CustomUser
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile_user"


class ProfileUpdateView(OwnProfileMixin, UpdateView):
    """Allow the currently logged-in user to update their own profile details."""

    model = CustomUser
    form_class = UserProfileUpdateForm
    template_name = "accounts/profile_form.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Could not update your profile. Please fix the errors below.",
        )
        return super().form_invalid(form)
