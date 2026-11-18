"""Views for ToolUp registration, authentication, role dashboards, profiles, and booking flows."""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from bookings.models import Booking
from config.constants import CEBU_CITY_BARANGAY_NAMES, CEBU_CITY_BARANGAY_SET, TIME_SLOTS
from reviews.models import Review
from services.models import ServiceCategory
from technicians.models import TechnicianProfile, VerificationDocument

from .forms import CustomLoginForm, CustomUserRegistrationForm, UserProfileUpdateForm
from .mixins import AdminRequiredMixin, ClientRequiredMixin, TechnicianRequiredMixin
from .models import CustomUser
from .ui_data import (
    TIME_SLOT_LABELS,
    build_readiness_list,
    ensure_default_categories,
    ensure_technician_profile,
    filter_verified_technicians,
    get_categories_with_counts,
    get_taken_slots,
    serialize_booking,
    serialize_document,
    serialize_review,
    serialize_technician,
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
        ensure_default_categories()
        featured = filter_verified_technicians()[:3]
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["featured_technicians"] = featured
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
        if self.object.role == CustomUser.Role.TECHNICIAN:
            ensure_technician_profile(self.object)
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
        qs = (
            Booking.objects.select_related(
                "client",
                "technician__user",
                "technician__category",
                "review",
            )
            .filter(client=self.request.user)
            .order_by("-created_at", "-id")
        )
        if selected_status in set(Booking.Status.values):
            qs = qs.filter(status=selected_status)
        else:
            selected_status = ""

        context["barangay_count"] = len(CEBU_CITY_BARANGAY_NAMES)
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["selected_status"] = selected_status
        context["client_bookings"] = [serialize_booking(b) for b in qs]
        return context


class TechnicianDashboardView(TechnicianRequiredMixin, TemplateView):
    """Role-specific dashboard for local Technician (Handyman) accounts."""

    template_name = "accounts/technician_dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        profile = ensure_technician_profile(self.request.user)
        docs = VerificationDocument.objects.select_related(
            "technician__user", "technician__category"
        ).filter(technician=profile)
        reviews = Review.objects.select_related("client").filter(technician=profile)[:5]
        bookings = (
            Booking.objects.select_related(
                "client",
                "technician__user",
                "technician__category",
                "review",
            )
            .filter(technician=profile)
            .order_by("-created_at", "-id")
        )

        context["tech_profile"] = serialize_technician(profile)
        context["tech_documents"] = [serialize_document(d) for d in docs]
        context["tech_reviews"] = [serialize_review(r) for r in reviews]
        context["tech_bookings"] = [serialize_booking(b) for b in bookings]
        return context


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Role-specific dashboard for Platform Admin accounts and user access management."""

    template_name = "accounts/admin_dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        users_qs = CustomUser.objects.order_by("-date_joined", "username")
        pending_docs_qs = VerificationDocument.objects.select_related(
            "technician__user", "technician__category"
        ).filter(status=VerificationDocument.Status.PENDING)
        context["users_list"] = users_qs
        context["total_users"] = users_qs.count()
        context["client_count"] = users_qs.filter(role=CustomUser.Role.CLIENT).count()
        context["technician_count"] = users_qs.filter(role=CustomUser.Role.TECHNICIAN).count()
        context["active_users_count"] = users_qs.filter(is_active=True).count()
        context["pending_documents"] = [serialize_document(d) for d in pending_docs_qs]
        context["pending_docs_count"] = pending_docs_qs.count()
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
        ensure_default_categories()
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
        profile = (
            TechnicianProfile.objects.select_related("user", "category")
            .filter(pk=self.kwargs["pk"], is_verified=True, user__is_active=True)
            .first()
        )
        if profile is None:
            raise Http404("Verified technician profile not found.")

        taken = get_taken_slots(profile, timezone.localdate())
        reviews = Review.objects.select_related("client").filter(technician=profile)
        approved_labels = [
            doc.get_document_type_display()
            for doc in profile.verification_documents.filter(
                status=VerificationDocument.Status.APPROVED
            )
        ]

        context["technician"] = serialize_technician(profile, taken_slots=taken)
        context["reviews"] = [serialize_review(r) for r in reviews]
        context["time_slots"] = TIME_SLOTS
        context["verified_docs"] = approved_labels or [
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
        ensure_default_categories()
        profile = ensure_technician_profile(self.request.user)
        context["tech_profile"] = serialize_technician(profile)
        context["categories"] = get_categories_with_counts()
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        return context

    def post(self, request, *args, **kwargs):
        ensure_default_categories()
        profile = ensure_technician_profile(request.user)
        category_slug = request.POST.get("category", "").strip()
        barangay = request.POST.get("barangay", "").strip()
        raw_rate = request.POST.get("hourly_rate", "").strip()
        bio = request.POST.get("bio", "").strip()
        is_accepting = "is_accepting_bookings" in request.POST

        category = ServiceCategory.objects.filter(slug=category_slug).first()
        if category is None:
            messages.error(request, "Please choose a valid service category.")
            return self.get(request, *args, **kwargs)

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

        profile.category = category
        profile.barangay = barangay
        profile.hourly_rate = rate
        profile.bio = bio
        profile.is_accepting_bookings = is_accepting
        profile.save(
            update_fields=["category", "barangay", "hourly_rate", "bio", "is_accepting_bookings"]
        )
        messages.success(request, "Your service options have been saved.")
        return redirect("technician_profile_edit")


class TechnicianVerificationUploadView(TechnicianRequiredMixin, TemplateView):
    """Allow Technicians to upload Trade License, Barangay Clearance, and Government ID."""

    template_name = "technicians/verification_upload.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        profile = ensure_technician_profile(self.request.user)
        docs = list(
            VerificationDocument.objects.select_related(
                "technician__user", "technician__category"
            ).filter(technician=profile)
        )
        approved_types = {
            d.document_type for d in docs if d.status == VerificationDocument.Status.APPROVED
        }
        approved_count = len(approved_types)
        context["documents"] = [serialize_document(d) for d in docs]
        context["approved_count"] = approved_count
        context["progress_percent"] = int((approved_count / 3) * 100)
        return context

    def post(self, request, *args, **kwargs):
        profile = ensure_technician_profile(request.user)
        doc_type = request.POST.get("document_type", "").strip()
        uploaded_file = request.FILES.get("file_path")

        if doc_type not in set(VerificationDocument.DocumentType.values):
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

        VerificationDocument.objects.update_or_create(
            technician=profile,
            document_type=doc_type,
            defaults={
                "file_path": uploaded_file,
                "status": VerificationDocument.Status.PENDING,
                "rejection_reason": "",
            },
        )
        messages.success(
            request,
            f"Credential '{uploaded_file.name}' uploaded and queued for Admin review.",
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

        base_qs = VerificationDocument.objects.select_related(
            "technician__user", "technician__category"
        )
        docs_qs = base_qs if selected_status == "ALL" else base_qs.filter(status=selected_status)

        context["selected_status"] = selected_status
        context["documents"] = [serialize_document(d) for d in docs_qs]
        context["counts"] = {
            "PENDING": base_qs.filter(status=VerificationDocument.Status.PENDING).count(),
            "APPROVED": base_qs.filter(status=VerificationDocument.Status.APPROVED).count(),
            "REJECTED": base_qs.filter(status=VerificationDocument.Status.REJECTED).count(),
        }
        context["readiness_list"] = build_readiness_list()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()

        if action == "approve_doc":
            doc = get_object_or_404(VerificationDocument, pk=request.POST.get("doc_id"))
            doc.status = VerificationDocument.Status.APPROVED
            doc.rejection_reason = ""
            doc.save(update_fields=["status", "rejection_reason"])
            messages.success(request, f"Approved {doc.get_document_type_display()} for {doc.technician}.")

        elif action == "reject_doc":
            doc = get_object_or_404(VerificationDocument, pk=request.POST.get("doc_id"))
            reason = request.POST.get("rejection_reason", "").strip()
            if not reason:
                messages.error(request, "A rejection reason is required when rejecting a document.")
                return redirect("admin_verification_queue")
            doc.status = VerificationDocument.Status.REJECTED
            doc.rejection_reason = reason
            doc.save(update_fields=["status", "rejection_reason"])
            messages.warning(request, f"Rejected {doc.get_document_type_display()} with reason: {reason}")

        elif action == "verify_technician":
            tech = get_object_or_404(TechnicianProfile, pk=request.POST.get("tech_id"))
            approved_types = set(
                tech.verification_documents.filter(
                    status=VerificationDocument.Status.APPROVED
                ).values_list("document_type", flat=True)
            )
            required_types = set(VerificationDocument.DocumentType.values)
            if not required_types.issubset(approved_types):
                messages.error(
                    request,
                    "All three required documents must be APPROVED before verifying this technician.",
                )
                return redirect("admin_verification_queue")
            tech.is_verified = True
            tech.save(update_fields=["is_verified"])
            messages.success(request, f"{tech} is now verified and listed in the directory.")

        else:
            messages.error(request, "Unsupported verification queue action.")

        return redirect("admin_verification_queue")


class BookingCreateView(ClientRequiredMixin, TemplateView):
    """Client form to schedule an available date and fixed time slot with a verified technician."""

    template_name = "bookings/booking_form.html"

    def _get_technician_or_404(self) -> TechnicianProfile:
        profile = (
            TechnicianProfile.objects.select_related("user", "category")
            .filter(
                pk=self.kwargs["technician_id"],
                is_verified=True,
                is_accepting_bookings=True,
                user__is_active=True,
            )
            .first()
        )
        if profile is None:
            raise Http404("Bookable verified technician not found.")
        return profile

    def _resolve_selected_date(self) -> date:
        today = timezone.localdate()
        raw_date = (
            self.request.POST.get("service_date")
            or self.request.GET.get("date")
            or ""
        ).strip()
        if raw_date:
            try:
                parsed = date.fromisoformat(raw_date)
                if parsed >= today:
                    return parsed
            except ValueError:
                pass
        return today + timedelta(days=1)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        profile = self._get_technician_or_404()
        today = timezone.localdate()
        selected_date = self._resolve_selected_date()
        taken = set(get_taken_slots(profile, selected_date))

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

        context["technician"] = serialize_technician(profile, taken_slots=list(taken))
        context["barangays"] = CEBU_CITY_BARANGAY_NAMES
        context["slot_options"] = slot_options
        context["min_date"] = today.isoformat()
        context["default_date"] = selected_date.isoformat()
        return context

    def post(self, request, *args, **kwargs):
        profile = self._get_technician_or_404()
        service_date_raw = request.POST.get("service_date", "").strip()
        time_slot = request.POST.get("time_slot", "").strip()
        barangay = request.POST.get("barangay", "").strip()
        service_address = request.POST.get("service_address", "").strip()
        issue_description = request.POST.get("issue_description", "").strip()

        if profile.user_id == request.user.pk:
            messages.error(request, "You cannot book your own technician profile.")
            return self.get(request, *args, **kwargs)

        try:
            parsed_date = date.fromisoformat(service_date_raw)
            if parsed_date < timezone.localdate():
                raise ValueError()
        except ValueError:
            messages.error(request, "Service date must be today or a future date.")
            return self.get(request, *args, **kwargs)

        if time_slot not in TIME_SLOT_LABELS:
            messages.error(request, "Selected time slot is invalid.")
            return self.get(request, *args, **kwargs)

        if barangay not in CEBU_CITY_BARANGAY_SET or not service_address:
            messages.error(request, "Please provide a valid Cebu City barangay and street address.")
            return self.get(request, *args, **kwargs)

        if not issue_description:
            messages.error(request, "Please describe the household repair issue.")
            return self.get(request, *args, **kwargs)

        full_address = (
            service_address
            if barangay.lower() in service_address.lower()
            else f"{service_address} (Brgy. {barangay}, Cebu City)"
        )

        if time_slot in set(get_taken_slots(profile, parsed_date)):
            messages.error(request, "Selected time slot is already booked for this date.")
            return self.get(request, *args, **kwargs)

        try:
            with transaction.atomic():
                booking = Booking.objects.create(
                    client=request.user,
                    technician=profile,
                    service_date=parsed_date,
                    time_slot=time_slot,
                    service_address=full_address,
                    issue_description=issue_description,
                    status=Booking.Status.PENDING,
                )
        except IntegrityError:
            messages.error(request, "Selected time slot was just reserved. Please pick another slot.")
            return self.get(request, *args, **kwargs)

        messages.success(
            request,
            f"Booking #{booking.pk} created for {profile.user.get_full_name() or profile.user.username} on {service_date_raw} ({TIME_SLOT_LABELS[time_slot]}).",
        )
        return redirect("booking_detail", pk=booking.pk)


class BookingDetailView(LoginRequiredMixin, TemplateView):
    """Booking details view with strict ownership and Section 9 status transition controls."""

    template_name = "bookings/booking_detail.html"

    def _get_authorized_booking(self) -> Booking:
        booking = get_object_or_404(
            Booking.objects.select_related(
                "client",
                "technician__user",
                "technician__category",
                "review",
            ),
            pk=self.kwargs["pk"],
        )
        user = self.request.user
        is_owner_client = booking.client_id == user.pk
        is_owner_tech = booking.technician.user_id == user.pk
        if not (is_owner_client or is_owner_tech or user.is_admin_role):
            raise PermissionDenied("You do not have permission to view this booking.")
        return booking

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        booking = self._get_authorized_booking()
        context["booking"] = serialize_booking(booking)
        return context

    def post(self, request, *args, **kwargs):
        booking = self._get_authorized_booking()
        action = request.POST.get("action", "").strip()
        status = booking.status
        user = request.user
        next_target = request.POST.get("next", "").strip()

        def _redirect_after():
            if next_target == "dashboard":
                return redirect("accounts:dashboard")
            return redirect("booking_detail", pk=booking.pk)

        if status in {Booking.Status.COMPLETED, Booking.Status.CANCELLED}:
            messages.error(request, f"Booking #{booking.pk} is already {status} and cannot be changed.")
            return _redirect_after()

        is_owner_tech = user.is_technician and booking.technician.user_id == user.pk
        is_owner_client = user.is_client and booking.client_id == user.pk

        if action in {"accept", "decline", "complete"} and not is_owner_tech:
            raise PermissionDenied("Only the assigned technician can perform this transition.")

        if action == "cancel" and not (is_owner_client or is_owner_tech):
            raise PermissionDenied("Only the booking client or assigned technician can cancel a booking.")

        valid_transitions = {
            (Booking.Status.PENDING, "accept"): Booking.Status.ACCEPTED,
            (Booking.Status.PENDING, "decline"): Booking.Status.CANCELLED,
            (Booking.Status.PENDING, "cancel"): Booking.Status.CANCELLED,
            (Booking.Status.ACCEPTED, "complete"): Booking.Status.COMPLETED,
            (Booking.Status.ACCEPTED, "cancel"): Booking.Status.CANCELLED,
        }
        next_status = valid_transitions.get((status, action))
        if next_status is None:
            messages.error(request, f"Transition '{action}' is not allowed from {status}.")
            return _redirect_after()

        booking.status = next_status
        booking.save(update_fields=["status"])
        messages.success(
            request,
            f"Booking #{booking.pk} updated: {status} -> {next_status}.",
        )
        return _redirect_after()


class ReviewCreateView(ClientRequiredMixin, TemplateView):
    """Client review and 1-5 star rating form for a COMPLETED booking."""

    template_name = "reviews/review_form.html"

    def _get_completed_booking_or_404(self) -> Booking:
        booking = get_object_or_404(
            Booking.objects.select_related(
                "client",
                "technician__user",
                "technician__category",
                "review",
            ),
            pk=self.kwargs["booking_id"],
        )
        if booking.client_id != self.request.user.pk:
            raise PermissionDenied("You can only review your own completed bookings.")
        if booking.status != Booking.Status.COMPLETED:
            raise Http404("Completed booking not found for review.")
        return booking

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        booking = self._get_completed_booking_or_404()
        context["booking"] = serialize_booking(booking)
        return context

    def post(self, request, *args, **kwargs):
        booking = self._get_completed_booking_or_404()
        if hasattr(booking, "review"):
            messages.error(request, "You have already submitted a review for this booking.")
            return redirect("booking_detail", pk=booking.pk)

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

        Review.objects.create(
            booking=booking,
            client=request.user,
            technician=booking.technician,
            rating=rating,
            comment=comment,
        )
        tech_name = booking.technician.user.get_full_name() or booking.technician.user.username
        messages.success(
            request,
            f"Thank you! Your {rating}-star review for {tech_name} has been published.",
        )
        return redirect("technician_detail", pk=booking.technician_id)
