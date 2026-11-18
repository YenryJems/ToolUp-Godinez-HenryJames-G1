# ToolUp — Verified Cebu City Handyman Directory & Booking Platform

ToolUp is a Django + PostgreSQL (Supabase) web application that connects Cebu City homeowners with admin-verified local handymen across **Plumbing**, **Electrical**, and **IT Troubleshooting**. Technicians must submit trade licenses, Cebu City barangay clearances, and government IDs for admin approval before they appear in the public directory or accept bookings.

---

## Core Feature (Increment 2): Verified Technician Directory & Service Booking Lifecycle

1. **Categorized Cebu City Directory (`/directory/`)**: Homeowners filter admin-verified, booking-accepting technicians by trade category, keyword/household issue, and any of the **80 Cebu City barangays** (`config/constants.py`).
2. **Schedule & Double-Booking Guard (`/bookings/create/<technician_id>/`)**: Clients pick a future date and an open 2-hour time slot (`08:00-10:00`, `10:00-12:00`, `13:00-15:00`, `15:00-17:00`). Already booked `PENDING` or `ACCEPTED` slots are disabled in the UI and blocked at the database level via a conditional `UniqueConstraint` (`unique_active_booking_slot`).
3. **Role-Enforced Booking Transitions (`/bookings/<id>/` & Dashboards)**:
   - `PENDING -> ACCEPTED` (assigned Technician only)
   - `PENDING -> CANCELLED` (Client cancels or Technician declines)
   - `ACCEPTED -> COMPLETED` (assigned Technician only)
   - `ACCEPTED -> CANCELLED` (Client or assigned Technician)
   - `COMPLETED` / `CANCELLED` are terminal states.
4. **Admin Verification Queue (`/dashboard/admin/verifications/`)**: Admins review uploaded `TRADE_LICENSE`, `BARANGAY_CLEARANCE`, and `GOVERNMENT_ID` credentials, approve or reject with a required reason, and verify technicians (`is_verified = True`).
5. **Verified Client Reviews (`/reviews/create/<booking_id>/`)**: Clients leave one 1–5 star rating and comment on their own `COMPLETED` bookings, updating the technician's public profile and average rating.

---

## Prerequisites

- **Python** 3.12+ (tested on Python 3.13.1)
- **PostgreSQL** (Supabase-hosted) or local **SQLite** (automatic offline fallback)
- **pip**

---

## Setup & Run Steps

### 1. Clone and install dependencies
```powershell
git clone https://github.com/YenryJems/ToolUp-Godinez-HenryJames-G1.git
cd ToolUp-Godinez-HenryJames-G1
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment variables (`.env`)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
- **Local SQLite (default offline dev)**: Leave `DATABASE_URL` unset and keep `DB_PASSWORD=replace-with-supabase-db-password` (or blank `DB_HOST`/`DB_NAME`). Django automatically falls back to `db.sqlite3`.
- **Supabase PostgreSQL**: Set your `SECRET_KEY` and either `DATABASE_URL` or the individual `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, and `DB_SSLMODE=require` values in `.env`. *(Use the individual `DB_*` fields if your password contains `?`, `$`, or `+`.)*

### 3. Apply database migrations
```powershell
python manage.py migrate
```

### 4. Seed demo accounts and sample data
```powershell
python manage.py seed_test_accounts
```
This idempotently creates the 3 service categories, verified and unverified Cebu City technician profiles, sample bookings across statuses, a sample review, and one working account per role:

| Role | Username | Email | Password |
|---|---|---|---|
| **Admin** | `admin_demo` | `admin.demo@toolup.cebu.ph` | `ToolUpDemo2026!` |
| **Technician** | `tech_demo` | `tech.demo@toolup.cebu.ph` | `ToolUpDemo2026!` |
| **Client** | `client_demo` | `client.demo@toolup.cebu.ph` | `ToolUpDemo2026!` |

### 5. Run the development server
```powershell
python manage.py runserver
```
Open `http://127.0.0.1:8000/` in your browser.

---

## Running Tests & System Checks

```powershell
python manage.py check
python manage.py test
```
*(Tests automatically use SQLite unless `USE_POSTGRES_FOR_TESTS=1` is set.)*

---

## Project Layout

```text
toolup/          Django settings, root URLs, WSGI/ASGI entrypoints
config/          Shared Cebu City barangays (80) and fixed booking time slots
accounts/        CustomUser, auth, role mixins, dashboards, views, and seed command
services/        ServiceCategory model
technicians/     TechnicianProfile and VerificationDocument models
bookings/        Booking model with conditional active-slot unique constraint
reviews/         Review model with 1..5 rating check constraint
templates/       Bootstrap 5 base layout and per-app templates
static/          Custom CSS complementing Bootstrap 5
docs/            PD2 Implementation / Completion Report PDF
```
