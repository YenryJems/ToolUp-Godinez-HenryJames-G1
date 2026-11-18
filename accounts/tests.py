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
    """Verify ToolUp directory, profile, booking, verification, and review UI routes and permissions."""

    def setUp(self) -> None:
        self.password = "StrongPass2026!"
        self.client_user = CustomUser.objects.create_user(
            username="ui_client",
            email="ui_client@example.com",
            password=self.password,
            first_name="Clara",
            last_name="Cebu",
            role=CustomUser.Role.CLIENT,
        )
        self.tech_user = CustomUser.objects.create_user(
            username="ui_tech",
            email="ui_tech@example.com",
            password=self.password,
            first_name="Mateo",
            last_name="Handyman",
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

    def test_home_and_directory_filters_render_cleanly(self) -> None:
        home_resp = self.client.get(reverse("home"))
        self.assertEqual(home_resp.status_code, 200)
        self.assertContains(home_resp, "Quick Technician Search")

        dir_resp = self.client.get(reverse("directory"))
        self.assertEqual(dir_resp.status_code, 200)
        self.assertContains(dir_resp, "Mateo Villanueva")

        filtered_resp = self.client.get(
            reverse("directory"),
            {"category": "plumbing", "barangay": "Lahug", "q": "leak"},
        )
        self.assertEqual(filtered_resp.status_code, 200)
        self.assertContains(filtered_resp, "Mateo Villanueva")
        self.assertNotContains(filtered_resp, "Clarisse Mendoza")

        empty_resp = self.client.get(reverse("directory"), {"q": "nonexistent_xyz_issue"})
        self.assertEqual(empty_resp.status_code, 200)
        self.assertContains(empty_resp, "No Verified Technicians Match Your Filters")

    def test_technician_public_profile_renders_and_handles_missing(self) -> None:
        resp = self.client.get(reverse("technician_detail", args=[1]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mateo Villanueva")
        self.assertContains(resp, "08:00 AM - 10:00 AM")

        missing_resp = self.client.get(reverse("technician_detail", args=[9999]))
        self.assertEqual(missing_resp.status_code, 404)

    def test_technician_ui_routes_enforce_role_access(self) -> None:
        tech_urls = [
            reverse("technician_profile_edit"),
            reverse("technician_verification"),
        ]
        for url in tech_urls:
            self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.client_user)
        for url in tech_urls:
            self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.tech_user)
        for url in tech_urls:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_verification_queue_enforces_role_and_rejection_reason(self) -> None:
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
            {"doc_id": "201", "action": "reject_doc", "rejection_reason": ""},
            follow=True,
        )
        self.assertContains(reject_missing, "rejection reason is required")

    def test_booking_and_review_routes_enforce_role_and_transitions(self) -> None:
        book_url = reverse("booking_create", args=[1])
        review_url = reverse("review_create", args=[103])
        detail_url = reverse("booking_detail", args=[101])

        self.client.force_login(self.tech_user)
        self.assertEqual(self.client.get(book_url).status_code, 403)
        self.assertEqual(self.client.get(review_url).status_code, 403)
        self.assertEqual(self.client.get(detail_url).status_code, 200)

        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(book_url).status_code, 200)
        self.assertEqual(self.client.get(review_url).status_code, 200)
        self.assertEqual(self.client.get(detail_url).status_code, 200)
        self.assertEqual(
            self.client.post(detail_url, {"action": "accept"}).status_code,
            403,
        )


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

