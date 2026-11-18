"""Management command to idempotently seed test accounts and core booking demo data."""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser
from accounts.ui_data import ensure_default_categories
from bookings.models import Booking
from reviews.models import Review
from technicians.models import TechnicianProfile, VerificationDocument

DEMO_PASSWORD = "ToolUpDemo2026!"

TEST_ACCOUNTS = (
    {
        "username": "admin_demo",
        "email": "admin.demo@toolup.cebu.ph",
        "first_name": "Ada",
        "last_name": "Moderator",
        "role": CustomUser.Role.ADMIN,
        "contact_number": "0917-100-0001",
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
    {
        "username": "tech_demo",
        "email": "tech.demo@toolup.cebu.ph",
        "first_name": "Mateo",
        "last_name": "Villanueva",
        "role": CustomUser.Role.TECHNICIAN,
        "contact_number": "0917-200-0002",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "client_demo",
        "email": "client.demo@toolup.cebu.ph",
        "first_name": "Clara",
        "last_name": "Dela Cruz",
        "role": CustomUser.Role.CLIENT,
        "contact_number": "0917-300-0003",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
)

EXTRA_TECHNICIANS = (
    {
        "username": "tech_ramon",
        "email": "ramon.demo@toolup.cebu.ph",
        "first_name": "Ramon",
        "last_name": "Bautista",
        "contact_number": "0917-200-0011",
        "category_slug": "electrical",
        "barangay": "Mabolo",
        "hourly_rate": Decimal("500.00"),
        "bio": "Master residential electrician for tripping circuit breakers, outlet rewiring, ceiling fan mounting, and safety grounding.",
        "is_verified": True,
    },
    {
        "username": "tech_clarisse",
        "email": "clarisse.demo@toolup.cebu.ph",
        "first_name": "Clarisse",
        "last_name": "Mendoza",
        "contact_number": "0917-200-0012",
        "category_slug": "it-troubleshooting",
        "barangay": "Guadalupe",
        "hourly_rate": Decimal("480.00"),
        "bio": "Home network and workstation specialist for Wi-Fi dead zones, mesh router setup, laptop tune-ups, and printer sharing.",
        "is_verified": True,
    },
    {
        "username": "tech_dante",
        "email": "dante.demo@toolup.cebu.ph",
        "first_name": "Dante",
        "last_name": "Cabanero",
        "contact_number": "0917-200-0013",
        "category_slug": "plumbing",
        "barangay": "Talamban",
        "hourly_rate": Decimal("420.00"),
        "bio": "Specializes in bathroom drain unclogging, shower valve replacement, PVC pipe repairs, and leak detection.",
        "is_verified": True,
    },
    {
        "username": "tech_elena",
        "email": "elena.demo@toolup.cebu.ph",
        "first_name": "Elena",
        "last_name": "Navarro",
        "contact_number": "0917-200-0014",
        "category_slug": "electrical",
        "barangay": "Banilad",
        "hourly_rate": Decimal("520.00"),
        "bio": "Handles LED lighting retrofits, aircon dedicated outlets, voltage troubleshooting, and panel upgrades in Cebu City homes.",
        "is_verified": True,
    },
    {
        "username": "tech_paolo",
        "email": "paolo.demo@toolup.cebu.ph",
        "first_name": "Paolo",
        "last_name": "Soriano",
        "contact_number": "0917-200-0015",
        "category_slug": "it-troubleshooting",
        "barangay": "Apas",
        "hourly_rate": Decimal("460.00"),
        "bio": "Desktop repair, SSD upgrades, home office LAN cabling, and virus cleanup for homeowners and remote workers.",
        "is_verified": True,
    },
    {
        "username": "tech_marco",
        "email": "marco.demo@toolup.cebu.ph",
        "first_name": "Marco",
        "last_name": "Quijano",
        "contact_number": "0917-200-0016",
        "category_slug": "plumbing",
        "barangay": "Labangon",
        "hourly_rate": Decimal("400.00"),
        "bio": "Residential pipe fitting, faucet installation, and drain maintenance across South Cebu City.",
        "is_verified": False,
    },
)


def _upsert_user(spec: dict) -> tuple[CustomUser, bool]:
    username = spec["username"]
    defaults = {k: v for k, v in spec.items() if k != "username"}
    user, created = CustomUser.objects.update_or_create(
        username=username,
        defaults=defaults,
    )
    user.set_password(DEMO_PASSWORD)
    user.save()
    return user, created


class Command(BaseCommand):
    """Create or update test accounts, categories, verified profiles, bookings, and reviews."""

    help = "Idempotently seed test accounts and core booking demo data for all ToolUp roles."

    def handle(self, *args, **options) -> None:
        categories = {cat.slug: cat for cat in ensure_default_categories()}

        users: dict[str, CustomUser] = {}
        for spec in TEST_ACCOUNTS:
            user, created = _upsert_user(spec)
            users[user.username] = user
            verb = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(f"{verb} {user.role} test account: {user.username} ({user.email})")
            )

        # Primary demo technician profile (tech_demo)
        tech_demo_profile, _ = TechnicianProfile.objects.update_or_create(
            user=users["tech_demo"],
            defaults={
                "category": categories["plumbing"],
                "barangay": "Lahug",
                "bio": "Licensed residential plumber handling burst pipes, kitchen sink leaks, clogged drains, and water tank pressure checks.",
                "hourly_rate": Decimal("450.00"),
                "is_accepting_bookings": True,
                "is_verified": True,
            },
        )
        for doc_type, filename in (
            (VerificationDocument.DocumentType.TRADE_LICENSE, "verification_docs/tesda_nc2_villanueva.pdf"),
            (VerificationDocument.DocumentType.BARANGAY_CLEARANCE, "verification_docs/brgy_lahug_clearance.jpg"),
            (VerificationDocument.DocumentType.GOVERNMENT_ID, "verification_docs/gov_id_villanueva.png"),
        ):
            VerificationDocument.objects.update_or_create(
                technician=tech_demo_profile,
                document_type=doc_type,
                defaults={
                    "file_path": filename,
                    "status": VerificationDocument.Status.APPROVED,
                    "rejection_reason": "",
                },
            )

        # Additional verified and pending technicians for directory & admin queue
        extra_profiles: dict[str, TechnicianProfile] = {}
        for item in EXTRA_TECHNICIANS:
            user, _ = _upsert_user(
                {
                    "username": item["username"],
                    "email": item["email"],
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "role": CustomUser.Role.TECHNICIAN,
                    "contact_number": item["contact_number"],
                    "is_staff": False,
                    "is_superuser": False,
                    "is_active": True,
                }
            )
            profile, _ = TechnicianProfile.objects.update_or_create(
                user=user,
                defaults={
                    "category": categories[item["category_slug"]],
                    "barangay": item["barangay"],
                    "bio": item["bio"],
                    "hourly_rate": item["hourly_rate"],
                    "is_accepting_bookings": True,
                    "is_verified": item["is_verified"],
                },
            )
            extra_profiles[item["username"]] = profile

            if item["is_verified"]:
                for doc_type in VerificationDocument.DocumentType.values:
                    VerificationDocument.objects.update_or_create(
                        technician=profile,
                        document_type=doc_type,
                        defaults={
                            "file_path": f"verification_docs/{item['username']}_{doc_type.lower()}.pdf",
                            "status": VerificationDocument.Status.APPROVED,
                            "rejection_reason": "",
                        },
                    )
            else:
                VerificationDocument.objects.update_or_create(
                    technician=profile,
                    document_type=VerificationDocument.DocumentType.TRADE_LICENSE,
                    defaults={
                        "file_path": "verification_docs/tesda_plumbing_nc2_quijano.pdf",
                        "status": VerificationDocument.Status.PENDING,
                        "rejection_reason": "",
                    },
                )
                VerificationDocument.objects.update_or_create(
                    technician=profile,
                    document_type=VerificationDocument.DocumentType.BARANGAY_CLEARANCE,
                    defaults={
                        "file_path": "verification_docs/brgy_labangon_clearance.jpg",
                        "status": VerificationDocument.Status.APPROVED,
                        "rejection_reason": "",
                    },
                )
                VerificationDocument.objects.update_or_create(
                    technician=profile,
                    document_type=VerificationDocument.DocumentType.GOVERNMENT_ID,
                    defaults={
                        "file_path": "verification_docs/philsys_id_quijano.png",
                        "status": VerificationDocument.Status.REJECTED,
                        "rejection_reason": "ID photo is cropped on the right edge; please re-upload a clear full-frame scan.",
                    },
                )

        # Sample bookings across statuses for client_demo <-> tech_demo & extra technicians
        today = timezone.localdate()
        client_user = users["client_demo"]
        if not Booking.objects.filter(client=client_user).exists():
            pending_booking = Booking.objects.create(
                client=client_user,
                technician=tech_demo_profile,
                service_date=today + timedelta(days=2),
                time_slot="08:00-10:00",
                service_address="14 Salinas Drive, Brgy. Lahug, Cebu City",
                issue_description="Kitchen sink pipe leak under cabinet and slow drain.",
                status=Booking.Status.PENDING,
            )
            accepted_booking = Booking.objects.create(
                client=client_user,
                technician=tech_demo_profile,
                service_date=today + timedelta(days=3),
                time_slot="10:00-12:00",
                service_address="14 Salinas Drive, Brgy. Lahug, Cebu City",
                issue_description="Bathroom water pressure check and valve inspection.",
                status=Booking.Status.ACCEPTED,
            )
            completed_unreviewed = Booking.objects.create(
                client=client_user,
                technician=extra_profiles["tech_clarisse"],
                service_date=today - timedelta(days=2),
                time_slot="13:00-15:00",
                service_address="88 V. Rama Ave., Brgy. Guadalupe, Cebu City",
                issue_description="Home Wi-Fi mesh router setup and printer network troubleshooting.",
                status=Booking.Status.COMPLETED,
            )
            completed_reviewed = Booking.objects.create(
                client=client_user,
                technician=tech_demo_profile,
                service_date=today - timedelta(days=5),
                time_slot="15:00-17:00",
                service_address="14 Salinas Drive, Brgy. Lahug, Cebu City",
                issue_description="Replaced leaking bathroom faucet cartridge.",
                status=Booking.Status.COMPLETED,
            )
            Review.objects.create(
                booking=completed_reviewed,
                client=client_user,
                technician=tech_demo_profile,
                rating=5,
                comment="Arrived right on time in Lahug and fixed our leaking faucet cleanly.",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded sample bookings (#{pending_booking.pk}, #{accepted_booking.pk}, #{completed_unreviewed.pk}, #{completed_reviewed.pk}) and review."
                )
            )
