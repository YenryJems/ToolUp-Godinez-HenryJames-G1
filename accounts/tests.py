"""Tests for ToolUp account registration, authentication, role dashboards, and profiles."""

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import CustomUser


class AccountRegistrationTests(TestCase):
    """Verify registration validation, password hashing, and role restrictions."""

    def setUp(self) -> None:
        self.register_url = reverse("accounts:register")
        self.existing_user = CustomUser.objects.create_user(
            username="existing_cebu",
            email="existing@example.com",
            password="StrongPassword123!",
            first_name="Maria",
            last_name="Reyes",
            role=CustomUser.Role.CLIENT,
        )

    def test_valid_client_registration_hashes_password_and_redirects(self) -> None:
        response = self.client.post(
            self.register_url,
            data={
                "username": "lahug_homeowner",
                "first_name": "Juan",
                "last_name": "Dela Cruz",
                "email": "Juan.DelaCruz@example.com",
                "contact_number": "09171234567",
                "role": CustomUser.Role.CLIENT,
                "password1": "SafeCebuPass2026!",
                "password2": "SafeCebuPass2026!",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(response, "Account created successfully!")

        user = CustomUser.objects.get(username="lahug_homeowner")
        self.assertEqual(user.email, "juan.delacruz@example.com")
        self.assertEqual(user.role, CustomUser.Role.CLIENT)
        self.assertNotEqual(user.password, "SafeCebuPass2026!")
        self.assertTrue(user.check_password("SafeCebuPass2026!"))

    def test_valid_technician_registration(self) -> None:
        response = self.client.post(
            self.register_url,
            data={
                "username": "mabolo_plumber",
                "first_name": "Pedro",
                "last_name": "Santos",
                "email": "pedro.santos@example.com",
                "contact_number": "09181112222",
                "role": CustomUser.Role.TECHNICIAN,
                "password1": "SafeTechPass2026!",
                "password2": "SafeTechPass2026!",
            },
        )
        self.assertRedirects(response, reverse("accounts:login"))
        user = CustomUser.objects.get(username="mabolo_plumber")
        self.assertEqual(user.role, CustomUser.Role.TECHNICIAN)

    def test_registration_rejects_missing_required_fields_and_bad_email(self) -> None:
        response = self.client.post(
            self.register_url,
            data={
                "username": "bad_user",
                "first_name": "",
                "last_name": "",
                "email": "not-an-email",
                "role": CustomUser.Role.CLIENT,
                "password1": "SafeCebuPass2026!",
                "password2": "SafeCebuPass2026!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="bad_user").exists())
        self.assertContains(response, "Registration failed.")

    def test_registration_rejects_duplicate_username_and_email(self) -> None:
        response = self.client.post(
            self.register_url,
            data={
                "username": "EXISTING_CEBU",
                "first_name": "Ana",
                "last_name": "Lim",
                "email": "EXISTING@example.com",
                "role": CustomUser.Role.CLIENT,
                "password1": "SafeCebuPass2026!",
                "password2": "SafeCebuPass2026!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_registration_rejects_password_mismatch_and_admin_role(self) -> None:
        response = self.client.post(
            self.register_url,
            data={
                "username": "sneaky_admin",
                "first_name": "Sneaky",
                "last_name": "User",
                "email": "sneaky@example.com",
                "role": CustomUser.Role.ADMIN,
                "password1": "SafeCebuPass2026!",
                "password2": "DifferentPass2026!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="sneaky_admin").exists())

    def test_database_enforces_unique_email(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            CustomUser.objects.create_user(
                username="another_username",
                email="existing@example.com",
                password="StrongPassword123!",
                first_name="Dup",
                last_name="Email",
                role=CustomUser.Role.CLIENT,
            )


class AuthenticationAndRoleDashboardTests(TestCase):
    """Verify login, logout, anonymous redirect protection, and role dashboard isolation."""

    def setUp(self) -> None:
        self.password = "StrongPass2026!"
        self.client_user = CustomUser.objects.create_user(
            username="client_one",
            email="client1@example.com",
            password=self.password,
            first_name="Clara",
            last_name="Client",
            role=CustomUser.Role.CLIENT,
        )
        self.tech_user = CustomUser.objects.create_user(
            username="tech_one",
            email="tech1@example.com",
            password=self.password,
            first_name="Tony",
            last_name="Tech",
            role=CustomUser.Role.TECHNICIAN,
        )
        self.admin_user = CustomUser.objects.create_user(
            username="admin_one",
            email="admin1@example.com",
            password=self.password,
            first_name="Ada",
            last_name="Admin",
            role=CustomUser.Role.ADMIN,
        )

    def test_invalid_login_shows_error_message(self) -> None:
        response = self.client.post(
            reverse("accounts:login"),
            data={"username": "client_one", "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_routes_each_role_to_correct_dashboard(self) -> None:
        role_targets = [
            (self.client_user, reverse("accounts:client_dashboard"), "Client Dashboard"),
            (self.tech_user, reverse("accounts:technician_dashboard"), "Technician Dashboard"),
            (self.admin_user, reverse("accounts:admin_dashboard"), "Admin Dashboard"),
        ]
        for user, expected_url, expected_heading in role_targets:
            self.client.logout()
            response = self.client.post(
                reverse("accounts:login"),
                data={"username": user.username, "password": self.password},
                follow=True,
            )
            self.assertRedirects(response, expected_url)
            self.assertContains(response, expected_heading)

    def test_logout_terminates_session_and_redirects_to_login(self) -> None:
        self.client.force_login(self.client_user)
        response = self.client.post(reverse("accounts:logout"), follow=True)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(response, "logged out")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_users_redirect_to_login_for_protected_pages(self) -> None:
        protected_urls = [
            reverse("accounts:dashboard"),
            reverse("accounts:client_dashboard"),
            reverse("accounts:technician_dashboard"),
            reverse("accounts:admin_dashboard"),
            reverse("accounts:profile"),
            reverse("accounts:profile_edit"),
        ]
        login_url = reverse("accounts:login")
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response["Location"].startswith(login_url))

    def test_users_cannot_access_other_roles_dashboards(self) -> None:
        # Client trying Technician and Admin dashboards
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(reverse("accounts:technician_dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:admin_dashboard")).status_code, 403)

        # Technician trying Client and Admin dashboards
        self.client.force_login(self.tech_user)
        self.assertEqual(self.client.get(reverse("accounts:client_dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:admin_dashboard")).status_code, 403)

        # Admin trying Client and Technician dashboards
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(reverse("accounts:client_dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:technician_dashboard")).status_code, 403)

    def test_admin_can_toggle_user_active_and_non_admin_is_blocked(self) -> None:
        toggle_url = reverse("accounts:admin_toggle_user", args=[self.client_user.pk])

        self.client.force_login(self.tech_user)
        self.assertEqual(self.client.post(toggle_url).status_code, 403)

        self.client.force_login(self.admin_user)
        response = self.client.post(toggle_url, follow=True)
        self.assertRedirects(response, reverse("accounts:admin_dashboard"))
        self.client_user.refresh_from_db()
        self.assertFalse(self.client_user.is_active)


class UserProfileTests(TestCase):
    """Verify profile viewing, editing, validation, and strict ownership enforcement."""

    def setUp(self) -> None:
        self.user_a = CustomUser.objects.create_user(
            username="user_a",
            email="user_a@example.com",
            password="StrongPass2026!",
            first_name="Alice",
            last_name="Tan",
            contact_number="09170000001",
            role=CustomUser.Role.CLIENT,
        )
        self.user_b = CustomUser.objects.create_user(
            username="user_b",
            email="user_b@example.com",
            password="StrongPass2026!",
            first_name="Bob",
            last_name="Lim",
            contact_number="09170000002",
            role=CustomUser.Role.TECHNICIAN,
        )

    def test_user_can_view_and_update_own_profile(self) -> None:
        self.client.force_login(self.user_a)

        detail_resp = self.client.get(reverse("accounts:profile"))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "Alice")
        self.assertContains(detail_resp, "user_a@example.com")

        own_by_id = self.client.get(reverse("accounts:profile_by_id", args=[self.user_a.pk]))
        self.assertEqual(own_by_id.status_code, 200)

        update_resp = self.client.post(
            reverse("accounts:profile_edit"),
            data={
                "first_name": "Alicia",
                "last_name": "Tan-Uy",
                "email": "alicia.new@example.com",
                "contact_number": "09179998888",
            },
            follow=True,
        )
        self.assertRedirects(update_resp, reverse("accounts:profile"))
        self.assertContains(update_resp, "Your profile has been updated successfully.")

        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.first_name, "Alicia")
        self.assertEqual(self.user_a.last_name, "Tan-Uy")
        self.assertEqual(self.user_a.email, "alicia.new@example.com")
        self.assertEqual(self.user_a.contact_number, "09179998888")

    def test_profile_update_rejects_duplicate_email(self) -> None:
        self.client.force_login(self.user_a)
        response = self.client.post(
            reverse("accounts:profile_edit"),
            data={
                "first_name": "Alice",
                "last_name": "Tan",
                "email": "USER_B@example.com",
                "contact_number": "09170000001",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.email, "user_a@example.com")

    def test_user_cannot_view_or_edit_another_users_profile(self) -> None:
        self.client.force_login(self.user_a)

        view_other = self.client.get(reverse("accounts:profile_by_id", args=[self.user_b.pk]))
        self.assertEqual(view_other.status_code, 403)

        edit_other_get = self.client.get(
            reverse("accounts:profile_edit_by_id", args=[self.user_b.pk])
        )
        self.assertEqual(edit_other_get.status_code, 403)

        edit_other_post = self.client.post(
            reverse("accounts:profile_edit_by_id", args=[self.user_b.pk]),
            data={
                "first_name": "Hacked",
                "last_name": "Name",
                "email": "hacked@example.com",
                "contact_number": "0000",
            },
        )
        self.assertEqual(edit_other_post.status_code, 403)
        self.user_b.refresh_from_db()
        self.assertEqual(self.user_b.first_name, "Bob")


class ToolUpUIRoutesTests(TestCase):
    """Verify database-backed directory, booking lifecycle, double-booking guard, verification, and reviews."""

    def setUp(self) -> None:
        from datetime import timedelta
        from decimal import Decimal
        from django.utils import timezone
        from bookings.models import Booking
        from services.models import ServiceCategory
        from technicians.models import TechnicianProfile, VerificationDocument

        self.password = "StrongPass2026!"
        self.client_user = CustomUser.objects.create_user(
            username="ui_client",
            email="ui_client@example.com",
            password=self.password,
            first_name="Clara",
            last_name="Cebu",
            role=CustomUser.Role.CLIENT,
        )
        self.other_client = CustomUser.objects.create_user(
            username="other_client",
            email="other_client@example.com",
            password=self.password,
            first_name="Marco",
            last_name="Homeowner",
            role=CustomUser.Role.CLIENT,
        )
        self.tech_user = CustomUser.objects.create_user(
            username="ui_tech",
            email="ui_tech@example.com",
            password=self.password,
            first_name="Mateo",
            last_name="Villanueva",
            role=CustomUser.Role.TECHNICIAN,
        )
        self.unverified_tech_user = CustomUser.objects.create_user(
            username="unverified_tech",
            email="unverified_tech@example.com",
            password=self.password,
            first_name="Clarisse",
            last_name="Mendoza",
            role=CustomUser.Role.TECHNICIAN,
        )
        self.admin_user = CustomUser.objects.create_user(
            username="ui_admin",
            email="ui_admin@example.com",
            password=self.password,
            first_name="Ada",
            last_name="Mod",
            role=CustomUser.Role.ADMIN,
        )

        self.plumbing = ServiceCategory.objects.create(
            name="Plumbing",
            slug="plumbing",
            icon="bi-droplet-fill",
            description="Pipe leaks and clogged drains.",
        )
        self.it_cat = ServiceCategory.objects.create(
            name="IT Troubleshooting",
            slug="it-troubleshooting",
            icon="bi-pc-display",
            description="Wi-Fi and router troubleshooting.",
        )

        self.tech_profile = TechnicianProfile.objects.create(
            user=self.tech_user,
            category=self.plumbing,
            barangay="Lahug",
            bio="Handles burst pipe leaks and clogged kitchen drains.",
            hourly_rate=Decimal("450.00"),
            is_accepting_bookings=True,
            is_verified=True,
        )
        self.unverified_profile = TechnicianProfile.objects.create(
            user=self.unverified_tech_user,
            category=self.it_cat,
            barangay="Guadalupe",
            bio="Home Wi-Fi setup specialist.",
            hourly_rate=Decimal("480.00"),
            is_accepting_bookings=True,
            is_verified=False,
        )
        self.pending_doc = VerificationDocument.objects.create(
            technician=self.unverified_profile,
            document_type=VerificationDocument.DocumentType.TRADE_LICENSE,
            file_path="verification_docs/test_license.pdf",
            status=VerificationDocument.Status.PENDING,
        )

        today = timezone.localdate()
        self.future_date = today + timedelta(days=2)
        self.pending_booking = Booking.objects.create(
            client=self.client_user,
            technician=self.tech_profile,
            service_date=self.future_date,
            time_slot="08:00-10:00",
            service_address="14 Salinas Drive, Brgy. Lahug, Cebu City",
            issue_description="Leaking kitchen faucet.",
            status=Booking.Status.PENDING,
        )
        self.completed_booking = Booking.objects.create(
            client=self.client_user,
            technician=self.tech_profile,
            service_date=today - timedelta(days=1),
            time_slot="13:00-15:00",
            service_address="14 Salinas Drive, Brgy. Lahug, Cebu City",
            issue_description="Bathroom drain repair.",
            status=Booking.Status.COMPLETED,
        )

    def test_home_and_directory_filters_only_verified_technicians(self) -> None:
        home_resp = self.client.get(reverse("home"))
        self.assertEqual(home_resp.status_code, 200)
        self.assertContains(home_resp, "Quick Technician Search")

        dir_resp = self.client.get(reverse("directory"))
        self.assertEqual(dir_resp.status_code, 200)
        self.assertContains(dir_resp, "Mateo Villanueva")
        self.assertNotContains(dir_resp, "Clarisse Mendoza")

        filtered_resp = self.client.get(
            reverse("directory"),
            {"category": "plumbing", "barangay": "Lahug", "q": "leak"},
        )
        self.assertEqual(filtered_resp.status_code, 200)
        self.assertContains(filtered_resp, "Mateo Villanueva")

        empty_resp = self.client.get(reverse("directory"), {"q": "nonexistent_xyz_issue"})
        self.assertEqual(empty_resp.status_code, 200)
        self.assertContains(empty_resp, "No Verified Technicians Match Your Filters")

    def test_technician_public_profile_renders_and_hides_unverified(self) -> None:
        resp = self.client.get(reverse("technician_detail", args=[self.tech_profile.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mateo Villanueva")
        self.assertContains(resp, "08:00 AM - 10:00 AM")

        unverified_resp = self.client.get(
            reverse("technician_detail", args=[self.unverified_profile.pk])
        )
        self.assertEqual(unverified_resp.status_code, 404)

    def test_technician_ui_routes_enforce_role_and_save_service_options(self) -> None:
        edit_url = reverse("technician_profile_edit")
        verify_url = reverse("technician_verification")

        self.assertEqual(self.client.get(edit_url).status_code, 302)
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(edit_url).status_code, 403)
        self.assertEqual(self.client.get(verify_url).status_code, 403)

        self.client.force_login(self.tech_user)
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        self.assertEqual(self.client.get(verify_url).status_code, 200)

        save_resp = self.client.post(
            edit_url,
            {
                "category": "plumbing",
                "barangay": "Mabolo",
                "hourly_rate": "550.00",
                "bio": "Updated plumbing bio for Mabolo.",
                "is_accepting_bookings": "on",
            },
            follow=True,
        )
        self.assertRedirects(save_resp, edit_url)
        self.tech_profile.refresh_from_db()
        self.assertEqual(self.tech_profile.barangay, "Mabolo")
        self.assertEqual(str(self.tech_profile.hourly_rate), "550.00")

    def test_admin_verification_queue_approves_and_requires_rejection_reason(self) -> None:
        from technicians.models import VerificationDocument

        queue_url = reverse("admin_verification_queue")
        self.assertEqual(self.client.get(queue_url).status_code, 302)

        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(queue_url).status_code, 403)

        self.client.force_login(self.admin_user)
        resp = self.client.get(queue_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Admin Verification Queue")

        reject_missing = self.client.post(
            queue_url,
            {"doc_id": str(self.pending_doc.pk), "action": "reject_doc", "rejection_reason": ""},
            follow=True,
        )
        self.assertContains(reject_missing, "rejection reason is required")

        self.client.post(
            queue_url,
            {"doc_id": str(self.pending_doc.pk), "action": "approve_doc"},
        )
        self.pending_doc.refresh_from_db()
        self.assertEqual(self.pending_doc.status, VerificationDocument.Status.APPROVED)

    def test_end_to_end_booking_lifecycle_and_double_booking_guard(self) -> None:
        from datetime import timedelta
        from django.utils import timezone
        from bookings.models import Booking
        from reviews.models import Review

        book_url = reverse("booking_create", args=[self.tech_profile.pk])
        slot_date = timezone.localdate() + timedelta(days=5)

        # Technician cannot open client booking creation
        self.client.force_login(self.tech_user)
        self.assertEqual(self.client.get(book_url).status_code, 403)

        # Client creates a new booking in DB
        self.client.force_login(self.client_user)
        create_resp = self.client.post(
            book_url,
            {
                "service_date": slot_date.isoformat(),
                "time_slot": "10:00-12:00",
                "barangay": "Lahug",
                "service_address": "99 Gorordo Ave",
                "issue_description": "Broken kitchen valve.",
            },
            follow=True,
        )
        created_booking = Booking.objects.get(
            technician=self.tech_profile,
            service_date=slot_date,
            time_slot="10:00-12:00",
        )
        self.assertEqual(created_booking.status, Booking.Status.PENDING)
        self.assertRedirects(create_resp, reverse("booking_detail", args=[created_booking.pk]))

        # Double-booking the same slot is rejected by backend and database constraint
        dup_resp = self.client.post(
            book_url,
            {
                "service_date": slot_date.isoformat(),
                "time_slot": "10:00-12:00",
                "barangay": "Lahug",
                "service_address": "100 Gorordo Ave",
                "issue_description": "Another leak.",
            },
        )
        self.assertEqual(dup_resp.status_code, 200)
        self.assertEqual(
            Booking.objects.filter(
                technician=self.tech_profile,
                service_date=slot_date,
                time_slot="10:00-12:00",
            ).count(),
            1,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(
                client=self.other_client,
                technician=self.tech_profile,
                service_date=slot_date,
                time_slot="10:00-12:00",
                service_address="Lahug",
                issue_description="Direct DB double-book attempt",
                status=Booking.Status.PENDING,
            )

        # Unrelated client cannot view or mutate the booking (403)
        detail_url = reverse("booking_detail", args=[created_booking.pk])
        self.client.force_login(self.other_client)
        self.assertEqual(self.client.get(detail_url).status_code, 403)

        # Booking owner client cannot accept their own booking (403)
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.post(detail_url, {"action": "accept"}).status_code, 403)

        # Assigned technician accepts and completes the booking
        self.client.force_login(self.tech_user)
        self.client.post(detail_url, {"action": "accept"})
        created_booking.refresh_from_db()
        self.assertEqual(created_booking.status, Booking.Status.ACCEPTED)

        self.client.post(detail_url, {"action": "complete"})
        created_booking.refresh_from_db()
        self.assertEqual(created_booking.status, Booking.Status.COMPLETED)

        # Client submits a 5-star review on the completed booking
        self.client.force_login(self.client_user)
        review_url = reverse("review_create", args=[created_booking.pk])
        rev_resp = self.client.post(
            review_url,
            {"rating": "5", "comment": "Prompt and fixed the valve neatly."},
            follow=True,
        )
        self.assertRedirects(rev_resp, reverse("technician_detail", args=[self.tech_profile.pk]))
        self.assertEqual(Review.objects.filter(booking=created_booking, rating=5).count(), 1)
        self.assertContains(rev_resp, "Prompt and fixed the valve neatly.")


class DatabaseConfigurationTests(TestCase):
    """Verify Supabase PostgreSQL and SQLite fallback environment configuration."""

    def test_falls_back_to_sqlite_when_postgres_vars_unset(self) -> None:
        from pathlib import Path
        from toolup.settings import build_database_config

        cfg = build_database_config({}, Path("/tmp/project"))
        self.assertEqual(cfg["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(cfg["NAME"], Path("/tmp/project/db.sqlite3"))

    def test_parses_supabase_database_url_and_transaction_pooler(self) -> None:
        from pathlib import Path
        from toolup.settings import build_database_config

        cfg = build_database_config(
            {
                "DATABASE_URL": "postgresql://postgres.abc123:p%40ss%23word@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require",
            },
            Path("/tmp/project"),
        )
        self.assertEqual(cfg["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(cfg["NAME"], "postgres")
        self.assertEqual(cfg["USER"], "postgres.abc123")
        self.assertEqual(cfg["PASSWORD"], "p@ss#word")
        self.assertEqual(cfg["HOST"], "aws-0-ap-southeast-1.pooler.supabase.com")
        self.assertEqual(cfg["PORT"], "6543")
        self.assertTrue(cfg["DISABLE_SERVER_SIDE_CURSORS"])
        self.assertEqual(cfg["CONN_MAX_AGE"], 0)
        self.assertEqual(cfg["OPTIONS"]["sslmode"], "require")

    def test_parses_individual_db_fields_for_session_pooler(self) -> None:
        from pathlib import Path
        from toolup.settings import build_database_config

        cfg = build_database_config(
            {
                "DB_HOST": "aws-0-ap-southeast-1.pooler.supabase.com",
                "DB_NAME": "postgres",
                "DB_USER": "postgres.xyz789",
                "DB_PASSWORD": "secret",
                "DB_PORT": "5432",
            },
            Path("/tmp/project"),
        )
        self.assertEqual(cfg["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(cfg["PORT"], "5432")
        self.assertFalse(cfg["DISABLE_SERVER_SIDE_CURSORS"])
        self.assertEqual(cfg["OPTIONS"]["sslmode"], "require")

    def test_falls_back_to_sqlite_when_password_is_placeholder(self) -> None:
        from pathlib import Path
        from toolup.settings import build_database_config

        cfg = build_database_config(
            {
                "DB_HOST": "aws-0-ap-southeast-1.pooler.supabase.com",
                "DB_NAME": "postgres",
                "DB_PASSWORD": "replace-with-supabase-db-password",
            },
            Path("/tmp/project"),
        )
        self.assertEqual(cfg["ENGINE"], "django.db.backends.sqlite3")

    def test_uses_tmp_sqlite_on_vercel_when_postgres_unset(self) -> None:
        from pathlib import Path
        from toolup.settings import build_database_config

        cfg = build_database_config({"VERCEL": "1"}, Path("/var/task"))
        self.assertEqual(cfg["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(cfg["NAME"], Path("/tmp/db.sqlite3"))

    def test_vercel_wsgi_and_static_and_host_settings(self) -> None:
        from django.conf import settings
        from toolup import wsgi

        self.assertTrue(hasattr(wsgi, "app"))
        self.assertIs(wsgi.app, wsgi.application)
        self.assertIn(".vercel.app", settings.ALLOWED_HOSTS)
        self.assertIn("https://*.vercel.app", settings.CSRF_TRUSTED_ORIGINS)

        resp = self.client.get("/static/css/custom.css")
        try:
            self.assertEqual(resp.status_code, 200)
        finally:
            resp.close()


class SeedTestAccountsCommandTests(TestCase):
    """Verify seed_test_accounts seeds accounts, categories, profiles, bookings, and reviews idempotently."""

    def test_seed_test_accounts_creates_and_updates_three_roles(self) -> None:
        from io import StringIO
        from django.core.management import call_command
        from accounts.management.commands.seed_test_accounts import DEMO_PASSWORD
        from bookings.models import Booking
        from reviews.models import Review
        from services.models import ServiceCategory
        from technicians.models import TechnicianProfile

        out = StringIO()
        call_command("seed_test_accounts", stdout=out)
        user_count_first = CustomUser.objects.count()
        booking_count_first = Booking.objects.count()

        call_command("seed_test_accounts", stdout=out)
        self.assertEqual(CustomUser.objects.count(), user_count_first)
        self.assertEqual(Booking.objects.count(), booking_count_first)
        self.assertEqual(ServiceCategory.objects.count(), 3)
        self.assertGreaterEqual(TechnicianProfile.objects.filter(is_verified=True).count(), 6)
        self.assertEqual(Booking.objects.count(), 4)
        self.assertEqual(Review.objects.count(), 1)

        admin_u = CustomUser.objects.get(username="admin_demo")
        tech_u = CustomUser.objects.get(username="tech_demo")
        client_u = CustomUser.objects.get(username="client_demo")

        self.assertTrue(admin_u.is_admin_role)
        self.assertTrue(admin_u.is_superuser)
        self.assertTrue(tech_u.is_technician)
        self.assertTrue(client_u.is_client)
        self.assertTrue(admin_u.check_password(DEMO_PASSWORD))
        self.assertTrue(tech_u.check_password(DEMO_PASSWORD))
        self.assertTrue(client_u.check_password(DEMO_PASSWORD))

