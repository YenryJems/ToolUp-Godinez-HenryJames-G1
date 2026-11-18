"""ORM query and presentation serialization helpers for ToolUp views and templates."""

from datetime import date
from decimal import Decimal

from django.db.models import Avg, Count, Q
from django.utils import timezone

from bookings.models import Booking
from config.constants import CEBU_CITY_BARANGAY_NAMES, TIME_SLOTS
from reviews.models import Review
from services.models import ServiceCategory
from technicians.models import TechnicianProfile, VerificationDocument

TIME_SLOT_LABELS: dict[str, str] = dict(TIME_SLOTS)

DEFAULT_CATEGORIES: tuple[dict, ...] = (
    {
        "slug": "plumbing",
        "name": "Plumbing",
        "icon": "bi-droplet-fill",
        "description": "Pipe leaks, clogged drains, faucet replacements, toilet repairs, and water pump troubleshooting.",
    },
    {
        "slug": "electrical",
        "name": "Electrical",
        "icon": "bi-lightning-charge-fill",
        "description": "Circuit breakers, faulty outlets, lighting installation, panel inspection, and residential rewiring.",
    },
    {
        "slug": "it-troubleshooting",
        "name": "IT Troubleshooting",
        "icon": "bi-pc-display",
        "description": "Wi-Fi router setup, slow laptops, home printer networks, OS recovery, and workstation cabling.",
    },
)


def ensure_default_categories() -> list[ServiceCategory]:
    """Ensure the three core ToolUp service categories exist in the database."""
    categories = []
    for item in DEFAULT_CATEGORIES:
        cat, _ = ServiceCategory.objects.get_or_create(
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "icon": item["icon"],
                "description": item["description"],
            },
        )
        categories.append(cat)
    return categories


def ensure_technician_profile(user) -> TechnicianProfile:
    """Return or create a default TechnicianProfile for a Technician user."""
    profile = getattr(user, "technician_profile", None)
    if profile is not None:
        return profile
    categories = ensure_default_categories()
    default_category = categories[0]
    profile, _ = TechnicianProfile.objects.get_or_create(
        user=user,
        defaults={
            "category": default_category,
            "barangay": CEBU_CITY_BARANGAY_NAMES[35],  # Lahug
            "bio": "Local Cebu City handyman ready to configure trade specialties and verification documents.",
            "hourly_rate": Decimal("450.00"),
            "is_accepting_bookings": True,
            "is_verified": False,
        },
    )
    return profile


def _user_initials(user) -> str:
    first = (user.first_name or "").strip()
    last = (user.last_name or "").strip()
    if first and last:
        return f"{first[0]}{last[0]}".upper()
    name = (first or user.username or "TU").strip()
    return name[:2].upper()


def serialize_technician(
    profile: TechnicianProfile,
    taken_slots: list[str] | None = None,
    avg_rating_override: float | None = None,
    review_count_override: int | None = None,
) -> dict:
    """Serialize a TechnicianProfile instance into template context fields."""
    if avg_rating_override is None or review_count_override is None:
        agg = profile.technician_reviews.aggregate(
            avg=Avg("rating"),
            total=Count("id"),
        )
        avg_val = agg["avg"] or 0.0
        review_count = agg["total"] or 0
    else:
        avg_val = avg_rating_override or 0.0
        review_count = review_count_override or 0

    full_name = profile.user.get_full_name().strip() or profile.user.username
    return {
        "id": profile.pk,
        "full_name": full_name,
        "initials": _user_initials(profile.user),
        "category_slug": profile.category.slug,
        "category_name": profile.category.name,
        "barangay": profile.barangay,
        "bio": profile.bio,
        "hourly_rate": f"{profile.hourly_rate:.2f}",
        "avg_rating": f"{float(avg_val):.1f}",
        "review_count": review_count,
        "is_verified": profile.is_verified,
        "is_accepting_bookings": profile.is_accepting_bookings,
        "taken_slots": taken_slots if taken_slots is not None else [],
    }


def serialize_booking(booking: Booking) -> dict:
    """Serialize a Booking instance into template context fields."""
    tech_user = booking.technician.user
    client_user = booking.client
    has_review = hasattr(booking, "review")
    return {
        "id": booking.pk,
        "technician_id": booking.technician_id,
        "technician_name": tech_user.get_full_name().strip() or tech_user.username,
        "technician_barangay": booking.technician.barangay,
        "category_name": booking.technician.category.name,
        "hourly_rate": f"{booking.technician.hourly_rate:.2f}",
        "client_name": client_user.get_full_name().strip() or client_user.username,
        "client_contact": client_user.contact_number or "Not provided",
        "service_date": booking.service_date.isoformat(),
        "time_slot": booking.time_slot,
        "time_slot_label": TIME_SLOT_LABELS.get(booking.time_slot, booking.time_slot),
        "service_address": booking.service_address,
        "issue_description": booking.issue_description,
        "status": booking.status,
        "has_review": has_review,
        "created_at": timezone.localtime(booking.created_at).strftime("%b %d, %Y, %I:%M %p"),
    }


def serialize_document(doc: VerificationDocument) -> dict:
    """Serialize a VerificationDocument instance into template context fields."""
    tech = doc.technician
    file_name = doc.file_path.name.rsplit("/", 1)[-1] if doc.file_path else "uploaded_file"
    return {
        "id": doc.pk,
        "technician_id": tech.pk,
        "technician_name": tech.user.get_full_name().strip() or tech.user.username,
        "category_name": tech.category.name,
        "barangay": tech.barangay,
        "document_type": doc.document_type,
        "document_label": doc.get_document_type_display(),
        "file_name": file_name,
        "status": doc.status,
        "rejection_reason": doc.rejection_reason or "",
        "submitted_at": timezone.localtime(doc.submitted_at).strftime("%b %d, %Y"),
    }


def serialize_review(review: Review) -> dict:
    """Serialize a Review instance into template context fields."""
    return {
        "client_name": review.client.get_full_name().strip() or review.client.username,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": timezone.localtime(review.created_at).strftime("%b %d, %Y"),
    }


def get_categories_with_counts() -> list[dict]:
    """Return service categories annotated with verified, bookable technician counts."""
    qs = ServiceCategory.objects.annotate(
        tech_count=Count(
            "technicians",
            filter=Q(
                technicians__is_verified=True,
                technicians__is_accepting_bookings=True,
            ),
            distinct=True,
        )
    ).order_by("id")
    if not qs.exists():
        return [{**cat, "tech_count": 0} for cat in DEFAULT_CATEGORIES]
    return [
        {
            "slug": cat.slug,
            "name": cat.name,
            "icon": cat.icon,
            "description": cat.description,
            "tech_count": cat.tech_count,
        }
        for cat in qs
    ]


def filter_verified_technicians(
    query: str = "",
    category: str = "",
    barangay: str = "",
) -> list[dict]:
    """Query verified, accepting-booking technicians filtered by keyword, category, and barangay."""
    qs = (
        TechnicianProfile.objects.select_related("user", "category")
        .filter(is_verified=True, is_accepting_bookings=True, user__is_active=True)
        .annotate(
            avg_rating_val=Avg("technician_reviews__rating"),
            review_count_val=Count("technician_reviews", distinct=True),
        )
    )
    if category:
        qs = qs.filter(category__slug=category)
    if barangay:
        qs = qs.filter(barangay=barangay)
    q_norm = query.strip()
    if q_norm:
        qs = qs.filter(
            Q(bio__icontains=q_norm)
            | Q(category__name__icontains=q_norm)
            | Q(category__description__icontains=q_norm)
            | Q(user__first_name__icontains=q_norm)
            | Q(user__last_name__icontains=q_norm)
            | Q(barangay__icontains=q_norm)
        )
    return [
        serialize_technician(
            tech,
            avg_rating_override=tech.avg_rating_val,
            review_count_override=tech.review_count_val,
        )
        for tech in qs
    ]


def get_taken_slots(profile: TechnicianProfile, target_date: date) -> list[str]:
    """Return time slots currently reserved by PENDING or ACCEPTED bookings on target_date."""
    return list(
        Booking.objects.filter(
            technician=profile,
            service_date=target_date,
            status__in=[Booking.Status.PENDING, Booking.Status.ACCEPTED],
        ).values_list("time_slot", flat=True)
    )


def build_readiness_list() -> list[dict]:
    """Build per-technician document approval readiness rows for Admin Verification Queue."""
    profiles = TechnicianProfile.objects.select_related("user", "category").prefetch_related(
        "verification_documents"
    )
    rows = []
    for profile in profiles:
        latest_by_type: dict[str, str] = {}
        for doc in profile.verification_documents.all():
            if doc.document_type not in latest_by_type:
                latest_by_type[doc.document_type] = doc.status

        trade_status = latest_by_type.get(VerificationDocument.DocumentType.TRADE_LICENSE, "MISSING")
        brgy_status = latest_by_type.get(
            VerificationDocument.DocumentType.BARANGAY_CLEARANCE, "MISSING"
        )
        gov_status = latest_by_type.get(VerificationDocument.DocumentType.GOVERNMENT_ID, "MISSING")
        ready = (
            trade_status == VerificationDocument.Status.APPROVED
            and brgy_status == VerificationDocument.Status.APPROVED
            and gov_status == VerificationDocument.Status.APPROVED
        )
        rows.append(
            {
                "id": profile.pk,
                "technician_name": profile.user.get_full_name().strip() or profile.user.username,
                "category_name": profile.category.name,
                "barangay": profile.barangay,
                "trade_license": trade_status,
                "barangay_clearance": brgy_status,
                "government_id": gov_status,
                "is_verified": profile.is_verified,
                "ready_to_verify": ready,
            }
        )
    return rows
