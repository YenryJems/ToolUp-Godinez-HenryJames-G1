"""Forms for ToolUp user registration, login, and profile updates."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class BootstrapFormMixin:
    """Apply Bootstrap 5 form styling classes across widget types."""

    def _apply_bootstrap_classes(self) -> None:
        for field in self.fields.values():
            widget = field.widget
            css_class = "form-select" if isinstance(widget, forms.Select) else "form-control"
            existing = widget.attrs.get("class", "")
            if css_class not in existing:
                widget.attrs["class"] = f"{existing} {css_class}".strip()


class CustomUserRegistrationForm(BootstrapFormMixin, UserCreationForm):
    """Validate and create Client or Technician accounts with unique email and username."""

    PUBLIC_ROLE_CHOICES = (
        (CustomUser.Role.CLIENT, "Client (Homeowner)"),
        (CustomUser.Role.TECHNICIAN, "Technician (Handyman)"),
    )

    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    contact_number = forms.CharField(
        max_length=20,
        required=False,
        label="Contact Number",
        help_text="Optional mobile number (e.g., 0917-123-4567).",
    )
    role = forms.ChoiceField(
        choices=PUBLIC_ROLE_CHOICES,
        required=True,
        label="Account Type",
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "contact_number",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_username(self) -> str:
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise ValidationError("Username is required.")
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise ValidationError("An account with this username already exists.")
        return username

    def clean_first_name(self) -> str:
        first_name = self.cleaned_data.get("first_name", "").strip()
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self) -> str:
        last_name = self.cleaned_data.get("last_name", "").strip()
        if not last_name:
            raise ValidationError("Last name is required.")
        return last_name

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email address is required.")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_role(self) -> str:
        role = self.cleaned_data.get("role", "")
        allowed = {choice[0] for choice in self.PUBLIC_ROLE_CHOICES}
        if role not in allowed:
            raise ValidationError("Please select a valid account role (Client or Technician).")
        return role


class CustomLoginForm(BootstrapFormMixin, AuthenticationForm):
    """Bootstrap 5 authentication form with clear credential error messaging."""

    error_messages = {
        "invalid_login": "Invalid username or password. Please check your credentials and try again.",
        "inactive": "This account has been deactivated. Please contact a ToolUp administrator.",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class UserProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    """Allow an authenticated user to update their own basic profile details."""

    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "contact_number")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_first_name(self) -> str:
        first_name = self.cleaned_data.get("first_name", "").strip()
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self) -> str:
        last_name = self.cleaned_data.get("last_name", "").strip()
        if not last_name:
            raise ValidationError("Last name is required.")
        return last_name

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email address is required.")
        if (
            CustomUser.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError("Another account is already using this email address.")
        return email
