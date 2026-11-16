"""Role-based access control mixins for ToolUp views."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .models import CustomUser


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require an authenticated user holding one of the allowed platform roles."""

    allowed_roles: tuple[str, ...] = ()

    def test_func(self) -> bool:
        user = self.request.user
        if CustomUser.Role.ADMIN in self.allowed_roles and user.is_superuser:
            return True
        return user.role in self.allowed_roles

    def handle_no_permission(self):
        """Return 403 Forbidden for wrong-role authenticated users; redirect anonymous users."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().handle_no_permission()


class ClientRequiredMixin(RoleRequiredMixin):
    """Restrict view access strictly to Client (Homeowner) users."""

    allowed_roles = (CustomUser.Role.CLIENT,)


class TechnicianRequiredMixin(RoleRequiredMixin):
    """Restrict view access strictly to Technician (Handyman) users."""

    allowed_roles = (CustomUser.Role.TECHNICIAN,)


class AdminRequiredMixin(RoleRequiredMixin):
    """Restrict view access strictly to Admin users or superusers."""

    allowed_roles = (CustomUser.Role.ADMIN,)
