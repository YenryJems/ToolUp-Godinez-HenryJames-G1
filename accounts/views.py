"""Views for ToolUp registration, authentication, role dashboards, profiles, and UI flows."""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from config.constants import CEBU_CITY_BARANGAY_NAMES, CEBU_CITY_BARANGAY_SET, TIME_SLOTS

from .forms import CustomLoginForm, CustomUserRegistrationForm, UserProfileUpdateForm
from .mixins import AdminRequiredMixin, ClientRequiredMixin, TechnicianRequiredMixin
from .models import CustomUser
from .ui_data import (
    DEMO_BOOKINGS,
    DEMO_REVIEWS_BY_TECH,
    DEMO_TECH_READINESS,
    DEMO_TECHNICIANS,
    DEMO_VERIFICATION_DOCS,
    TIME_SLOT_LABELS,
    filter_verified_technicians,
    get_booking_by_id,
    get_categories_with_counts,
    get_technician_by_id,
)

ALLOWED_DOC_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_DOC_SIZE_BYTES = 5 * 1024 * 1024


class HomeView(TemplateView):
    """Landing view routing logged-in users to their dashboard and guests to ToolUp home."""

    template_name = "accounts/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["featured_technicians"] = DEMO_TECHNICIANS[:3]
        return context


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
        selected_status = self.request.GET.get("status", "").strip().upper()
        bookings = DEMO_BOOKINGS
        if selected_status in {"PENDING", "ACCEPTED", "COMPLETED", "CANCELLED"}:
            bookings = [b for b in DEMO_BOOKINGS if b["status"] == selected_status]
        else:
            selected_status = ""

        context["barangay_count"] = len(CEBU_CITY_BARANGAY_NAMES)
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["selected_status"] = selected_status
        context["client_bookings"] = bookings
        return context


class TechnicianDashboardView(TechnicianRequiredMixin, TemplateView):
    """Role-specific dashboard for local Technician (Handyman) accounts."""

    template_name = "accounts/technician_dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["tech_profile"] = DEMO_TECHNICIANS[0]
        context["tech_documents"] = [
            d for d in DEMO_VERIFICATION_DOCS if d["technician_id"] == 7
        ]
        context["tech_reviews"] = DEMO_REVIEWS_BY_TECH.get(1, [])
        context["tech_bookings"] = DEMO_BOOKINGS
        return context


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Role-specific dashboard for Platform Admin accounts and user access management."""

    template_name = "accounts/admin_dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        users_qs = CustomUser.objects.order_by("-date_joined", "username")
        pending_docs = [d for d in DEMO_VERIFICATION_DOCS if d["status"] == "PENDING"]
        context["users_list"] = users_qs
        context["total_users"] = users_qs.count()
        context["client_count"] = users_qs.filter(role=CustomUser.Role.CLIENT).count()
        context["technician_count"] = users_qs.filter(role=CustomUser.Role.TECHNICIAN).count()
        context["active_users_count"] = users_qs.filter(is_active=True).count()
        context["pending_documents"] = pending_docs
        context["pending_docs_count"] = len(pending_docs)
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


class ServiceDirectoryView(TemplateView):
    """Searchable and filterable Cebu City verified technician directory."""

    template_name = "services/directory.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        selected_category = self.request.GET.get("category", "").strip()
        selected_barangay = self.request.GET.get("barangay", "").strip()

        context["query"] = query
        context["selected_category"] = selected_category
        context["selected_barangay"] = selected_barangay
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["technicians"] = filter_verified_technicians(
            query=query,
            category=selected_category,
            barangay=selected_barangay,
        )
        return context


class TechnicianPublicProfileView(TemplateView):
    """Public profile view displaying a verified technician's bio, slots, and reviews."""

    template_name = "technicians/profile_detail.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        tech = get_technician_by_id(self.kwargs["pk"])
        if tech is None or not tech["is_verified"]:
            raise Http404("Verified technician profile not found.")
        context["technician"] = tech
        context["reviews"] = DEMO_REVIEWS_BY_TECH.get(tech["id"], [])
        context["time_slots"] = TIME_SLOTS
        context["verified_docs"] = [
            "Trade License",
            "Barangay Clearance",
            "Government ID",
        ]
        return context


class TechnicianServiceOptionsView(TechnicianRequiredMixin, TemplateView):
    """Allow Technicians to edit their service category, Cebu City barangay, bio, rate, and availability."""

    template_name = "technicians/profile_form.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["tech_profile"] = DEMO_TECHNICIANS[0]
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        return context

    def post(self, request, *args, **kwargs):
        barangay = request.POST.get("barangay", "").strip()
        raw_rate = request.POST.get("hourly_rate", "").strip()
        bio = request.POST.get("bio", "").strip()

        if barangay not in CEBU_CITY_BARANGAY_SET:
            messages.error(request, "Please select a valid Cebu City barangay.")
            return self.get(request, *args, **kwargs)

        try:
            rate = Decimal(raw_rate)
            if rate < 0:
                raise InvalidOperation()
        except (InvalidOperation, ValueError):
            messages.error(request, "Hourly rate must be a non-negative amount.")
            return self.get(request, *args, **kwargs)

        if not bio:
            messages.error(request, "Please enter a trade bio describing the issues you handle.")
            return self.get(request, *args, **kwargs)

        messages.success(
            request,
            "Service options validated! Persistent updates will save once the technicians module is connected.",
        )
        return redirect("technician_profile_edit")


class TechnicianVerificationUploadView(TechnicianRequiredMixin, TemplateView):
    """Allow Technicians to upload Trade License, Barangay Clearance, and Government ID."""

    template_name = "technicians/verification_upload.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        docs = [d for d in DEMO_VERIFICATION_DOCS if d["technician_id"] == 7]
        approved_count = sum(1 for d in docs if d["status"] == "APPROVED")
        context["documents"] = docs
        context["approved_count"] = approved_count
        context["progress_percent"] = int((approved_count / 3) * 100)
        return context

    def post(self, request, *args, **kwargs):
        doc_type = request.POST.get("document_type", "").strip()
        uploaded_file = request.FILES.get("file_path")

        if doc_type not in {"TRADE_LICENSE", "BARANGAY_CLEARANCE", "GOVERNMENT_ID"}:
            messages.error(request, "Invalid verification document type selected.")
            return self.get(request, *args, **kwargs)

        if uploaded_file is None:
            messages.error(request, "Please choose a PDF, JPG, or PNG file to upload.")
            return self.get(request, *args, **kwargs)

        ext = "." + uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
        if ext not in ALLOWED_DOC_EXTENSIONS:
            messages.error(request, "Unsupported file format. Allowed formats: PDF, JPG, PNG.")
            return self.get(request, *args, **kwargs)

        if uploaded_file.size > MAX_DOC_SIZE_BYTES:
            messages.error(request, "File exceeds the 5 MB maximum upload limit.")
            return self.get(request, *args, **kwargs)

        messages.success(
            request,
            f"Credential '{uploaded_file.name}' validated for {doc_type}. Persistent storage activates with the technicians module.",
        )
        return redirect("technician_verification")


class AdminVerificationQueueView(AdminRequiredMixin, TemplateView):
    """Admin review queue for approving/rejecting documents and verifying technicians."""

    template_name = "technicians/admin_verification_queue.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        selected_status = self.request.GET.get("status", "PENDING").strip().upper()
        if selected_status not in {"PENDING", "APPROVED", "REJECTED", "ALL"}:
            selected_status = "PENDING"

        docs = DEMO_VERIFICATION_DOCS
        if selected_status != "ALL":
            docs = [d for d in DEMO_VERIFICATION_DOCS if d["status"] == selected_status]

        context["selected_status"] = selected_status
        context["documents"] = docs
        context["counts"] = {
            "PENDING": sum(1 for d in DEMO_VERIFICATION_DOCS if d["status"] == "PENDING"),
            "APPROVED": sum(1 for d in DEMO_VERIFICATION_DOCS if d["status"] == "APPROVED"),
            "REJECTED": sum(1 for d in DEMO_VERIFICATION_DOCS if d["status"] == "REJECTED"),
        }
        context["readiness_list"] = DEMO_TECH_READINESS
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()
        if action == "approve_doc":
            messages.success(request, "Document marked APPROVED in preview queue.")
        elif action == "reject_doc":
            reason = request.POST.get("rejection_reason", "").strip()
            if not reason:
                messages.error(request, "A rejection reason is required when rejecting a document.")
                return redirect("admin_verification_queue")
            messages.warning(request, f"Document marked REJECTED with reason: {reason}")
        elif action == "verify_technician":
            messages.success(request, "Technician verification action recorded.")
        else:
            messages.error(request, "Unsupported verification queue action.")
        return redirect("admin_verification_queue")


class BookingCreateView(ClientRequiredMixin, TemplateView):
    """Client form to schedule an available date and fixed time slot with a verified technician."""

    template_name = "bookings/booking_form.html"

    def _get_technician_or_404(self) -> dict:
        tech = get_technician_by_id(self.kwargs["technician_id"])
        if tech is None or not tech["is_verified"] or not tech["is_accepting_bookings"]:
            raise Http404("Bookable verified technician not found.")
        return tech

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        tech = self._get_technician_or_404()
        today = timezone.localdate()
        taken = set(tech["taken_slots"])
        slot_options = []
        default_assigned = False
        for code, label in TIME_SLOTS:
            is_taken = code in taken
            is_default = (not is_taken) and (not default_assigned)
            if is_default:
                default_assigned = True
            slot_options.append(
                {
                    "code": code,
                    "label": label,
                    "is_taken": is_taken,
                    "is_default": is_default,
                }
            )

        context["technician"] = tech
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["slot_options"] = slot_options
        context["min_date"] = today.isoformat()
        context["default_date"] = (today + timedelta(days=1)).isoformat()
        return context

    def post(self, request, *args, **kwargs):
        tech = self._get_technician_or_404()
        service_date_raw = request.POST.get("service_date", "").strip()
        time_slot = request.POST.get("time_slot", "").strip()
        barangay = request.POST.get("barangay", "").strip()
        service_address = request.POST.get("service_address", "").strip()
        issue_description = request.POST.get("issue_description", "").strip()

        try:
            parsed_date = date.fromisoformat(service_date_raw)
            if parsed_date < timezone.localdate():
                raise ValueError()
        except ValueError:
            messages.error(request, "Service date must be today or a future date.")
            return self.get(request, *args, **kwargs)

        if time_slot not in TIME_SLOT_LABELS or time_slot in tech["taken_slots"]:
            messages.error(request, "Selected time slot is invalid or already booked.")
            return self.get(request, *args, **kwargs)

        if barangay not in CEBU_CITY_BARANGAY_SET or not service_address:
            messages.error(request, "Please provide a valid Cebu City barangay and street address.")
            return self.get(request, *args, **kwargs)

        if not issue_description:
            messages.error(request, "Please describe the household repair issue.")
            return self.get(request, *args, **kwargs)

        messages.success(
            request,
            f"Booking request validated for {tech['full_name']} on {service_date_raw} ({TIME_SLOT_LABELS[time_slot]}).",
        )
        return redirect("accounts:client_dashboard")


class BookingDetailView(LoginRequiredMixin, TemplateView):
    """Booking details view with Section 9 role-enforced status transition controls."""

    template_name = "bookings/booking_detail.html"

    def _get_booking_or_404(self) -> dict:
        booking = get_booking_by_id(self.kwargs["pk"])
        if booking is None:
            raise Http404("Booking not found.")
        return booking

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["booking"] = self._get_booking_or_404()
        return context

    def post(self, request, *args, **kwargs):
        booking = self._get_booking_or_404()
        action = request.POST.get("action", "").strip()
        status = booking["status"]
        user = request.user

        if status in {"COMPLETED", "CANCELLED"}:
            messages.error(request, f"Booking #{booking['id']} is already {status} and cannot be changed.")
            return redirect("booking_detail", pk=booking["id"])

        if action in {"accept", "decline", "complete"} and not user.is_technician:
            raise PermissionDenied("Only the assigned technician can perform this transition.")

        if action == "cancel" and not (user.is_client or user.is_technician):
            raise PermissionDenied("Only the booking client or technician can cancel a booking.")

        valid_transitions = {
            ("PENDING", "accept"): "ACCEPTED",
            ("PENDING", "decline"): "CANCELLED",
            ("PENDING", "cancel"): "CANCELLED",
            ("ACCEPTED", "complete"): "COMPLETED",
            ("ACCEPTED", "cancel"): "CANCELLED",
        }
        next_status = valid_transitions.get((status, action))
        if next_status is None:
            messages.error(request, f"Transition '{action}' is not allowed from {status}.")
            return redirect("booking_detail", pk=booking["id"])

        messages.success(
            request,
            f"Booking #{booking['id']} transition {status} -> {next_status} validated.",
        )
        return redirect("booking_detail", pk=booking["id"])


class ReviewCreateView(ClientRequiredMixin, TemplateView):
    """Client review and 1-5 star rating form for a COMPLETED booking."""

    template_name = "reviews/review_form.html"

    def _get_completed_booking_or_404(self) -> dict:
        booking = get_booking_by_id(self.kwargs["booking_id"])
        if booking is None or booking["status"] != "COMPLETED":
            raise Http404("Completed booking not found for review.")
        return booking

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["booking"] = self._get_completed_booking_or_404()
        return context

    def post(self, request, *args, **kwargs):
        booking = self._get_completed_booking_or_404()
        raw_rating = request.POST.get("rating", "").strip()
        comment = request.POST.get("comment", "").strip()

        try:
            rating = int(raw_rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            messages.error(request, "Rating must be a whole number from 1 to 5.")
            return self.get(request, *args, **kwargs)

        if not comment:
            messages.error(request, "Please enter a brief review comment.")
            return self.get(request, *args, **kwargs)

        messages.success(
            request,
            f"Thank you! Your {rating}-star review for {booking['technician_name']} has been validated.",
        )
        return redirect("accounts:client_dashboard")
