"""UI preview datasets and lookup helpers backed by Cebu City constants."""

from config.constants import CEBU_CITY_BARANGAY_NAMES, TIME_SLOTS

TIME_SLOT_LABELS: dict[str, str] = dict(TIME_SLOTS)

SERVICE_CATEGORIES: list[dict] = [
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
]

DEMO_TECHNICIANS: list[dict] = [
    {
        "id": 1,
        "full_name": "Mateo Villanueva",
        "initials": "MV",
        "category_slug": "plumbing",
        "category_name": "Plumbing",
        "barangay": "Lahug",
        "bio": "Licensed residential plumber handling burst pipes, kitchen sink leaks, clogged drains, and water tank pressure checks.",
        "hourly_rate": "450.00",
        "avg_rating": "4.9",
        "review_count": 14,
        "is_verified": True,
        "is_accepting_bookings": True,
        "taken_slots": ["10:00-12:00"],
    },
    {
        "id": 2,
        "full_name": "Ramon Bautista",
        "initials": "RB",
        "category_slug": "electrical",
        "category_name": "Electrical",
        "barangay": "Mabolo",
        "bio": "Master residential electrician for tripping circuit breakers, outlet rewiring, ceiling fan mounting, and safety grounding.",
        "hourly_rate": "500.00",
        "avg_rating": "4.8",
        "review_count": 11,
        "is_verified": True,
        "is_accepting_bookings": True,
        "taken_slots": ["08:00-10:00"],
    },
    {
        "id": 3,
        "full_name": "Clarisse Mendoza",
        "initials": "CM",
        "category_slug": "it-troubleshooting",
        "category_name": "IT Troubleshooting",
        "barangay": "Guadalupe",
        "bio": "Home network and workstation specialist for Wi-Fi dead zones, mesh router setup, laptop tune-ups, and printer sharing.",
        "hourly_rate": "480.00",
        "avg_rating": "5.0",
        "review_count": 9,
        "is_verified": True,
        "is_accepting_bookings": True,
        "taken_slots": ["13:00-15:00"],
    },
    {
        "id": 4,
        "full_name": "Dante Cabanero",
        "initials": "DC",
        "category_slug": "plumbing",
        "category_name": "Plumbing",
        "barangay": "Talamban",
        "bio": "Specializes in bathroom drain unclogging, shower valve replacement, PVC pipe repairs, and leak detection.",
        "hourly_rate": "420.00",
        "avg_rating": "4.7",
        "review_count": 8,
        "is_verified": True,
        "is_accepting_bookings": True,
        "taken_slots": [],
    },
    {
        "id": 5,
        "full_name": "Elena Navarro",
        "initials": "EN",
        "category_slug": "electrical",
        "category_name": "Electrical",
        "barangay": "Banilad",
        "bio": "Handles LED lighting retrofits, aircon dedicated outlets, voltage troubleshooting, and panel upgrades in Cebu City homes.",
        "hourly_rate": "520.00",
        "avg_rating": "4.9",
        "review_count": 12,
        "is_verified": True,
        "is_accepting_bookings": True,
        "taken_slots": ["15:00-17:00"],
    },
    {
        "id": 6,
        "full_name": "Paolo Soriano",
        "initials": "PS",
        "category_slug": "it-troubleshooting",
        "category_name": "IT Troubleshooting",
        "barangay": "Apas",
        "bio": "Desktop repair, SSD upgrades, home office LAN cabling, and virus cleanup for homeowners and remote workers.",
        "hourly_rate": "460.00",
        "avg_rating": "4.8",
        "review_count": 7,
        "is_verified": True,
        "is_accepting_bookings": True,
        "taken_slots": ["08:00-10:00", "13:00-15:00"],
    },
]

DEMO_REVIEWS_BY_TECH: dict[int, list[dict]] = {
    1: [
        {
            "client_name": "Carla D.",
            "rating": 5,
            "comment": "Arrived right on the 08:00-10:00 slot in Lahug and fixed our leaking kitchen P-trap cleanly.",
            "created_at": "Nov 12, 2026",
        },
        {
            "client_name": "Marco V.",
            "rating": 5,
            "comment": "Very transparent with parts and cleared our clogged bathroom floor drain in under an hour.",
            "created_at": "Nov 04, 2026",
        },
    ],
    2: [
        {
            "client_name": "Trisha L.",
            "rating": 5,
            "comment": "Found the faulty outlet causing our breaker to trip and replaced it safely.",
            "created_at": "Nov 10, 2026",
        },
    ],
    3: [
        {
            "client_name": "Jose R.",
            "rating": 5,
            "comment": "Set up our mesh Wi-Fi across both floors in Guadalupe and fixed our shared home printer.",
            "created_at": "Nov 14, 2026",
        },
    ],
}

DEMO_BOOKINGS: list[dict] = [
    {
        "id": 101,
        "technician_id": 1,
        "technician_name": "Mateo Villanueva",
        "technician_barangay": "Lahug",
        "category_name": "Plumbing",
        "hourly_rate": "450.00",
        "client_name": "Clara Homeowner",
        "client_contact": "0917-555-0101",
        "service_date": "2026-11-20",
        "time_slot": "08:00-10:00",
        "time_slot_label": TIME_SLOT_LABELS["08:00-10:00"],
        "service_address": "14 Salinas Drive, Brgy. Lahug, Cebu City",
        "issue_description": "Kitchen sink pipe leak under cabinet and slow drain.",
        "status": "PENDING",
        "has_review": False,
        "created_at": "Nov 18, 2026, 09:30 AM",
    },
    {
        "id": 102,
        "technician_id": 2,
        "technician_name": "Ramon Bautista",
        "technician_barangay": "Mabolo",
        "category_name": "Electrical",
        "hourly_rate": "500.00",
        "client_name": "Mark Resident",
        "client_contact": "0918-555-0202",
        "service_date": "2026-11-21",
        "time_slot": "10:00-12:00",
        "time_slot_label": TIME_SLOT_LABELS["10:00-12:00"],
        "service_address": "22 F. Cabahug St., Brgy. Mabolo, Cebu City",
        "issue_description": "Main bedroom outlet sparks when plugging appliances; breaker trips.",
        "status": "ACCEPTED",
        "has_review": False,
        "created_at": "Nov 17, 2026, 02:15 PM",
    },
    {
        "id": 103,
        "technician_id": 3,
        "technician_name": "Clarisse Mendoza",
        "technician_barangay": "Guadalupe",
        "category_name": "IT Troubleshooting",
        "hourly_rate": "480.00",
        "client_name": "Clara Homeowner",
        "client_contact": "0917-555-0101",
        "service_date": "2026-11-12",
        "time_slot": "13:00-15:00",
        "time_slot_label": TIME_SLOT_LABELS["13:00-15:00"],
        "service_address": "88 V. Rama Ave., Brgy. Guadalupe, Cebu City",
        "issue_description": "Home Wi-Fi router drops connection upstairs and printer is offline.",
        "status": "COMPLETED",
        "has_review": False,
        "created_at": "Nov 10, 2026, 11:00 AM",
    },
    {
        "id": 104,
        "technician_id": 4,
        "technician_name": "Dante Cabanero",
        "technician_barangay": "Talamban",
        "category_name": "Plumbing",
        "hourly_rate": "420.00",
        "client_name": "Liza Homeowner",
        "client_contact": "0919-555-0303",
        "service_date": "2026-11-10",
        "time_slot": "15:00-17:00",
        "time_slot_label": TIME_SLOT_LABELS["15:00-17:00"],
        "service_address": "5 Gov. M. Cuenco Ave., Brgy. Talamban, Cebu City",
        "issue_description": "Rescheduled bathroom faucet replacement.",
        "status": "CANCELLED",
        "has_review": False,
        "created_at": "Nov 08, 2026, 04:40 PM",
    },
]

DEMO_VERIFICATION_DOCS: list[dict] = [
    {
        "id": 201,
        "technician_id": 7,
        "technician_name": "Marco Quijano",
        "category_name": "Plumbing",
        "barangay": "Labangon",
        "document_type": "TRADE_LICENSE",
        "document_label": "Trade License / TESDA NC",
        "file_name": "tesda_plumbing_nc2_quijano.pdf",
        "status": "PENDING",
        "rejection_reason": "",
        "submitted_at": "Nov 18, 2026",
    },
    {
        "id": 202,
        "technician_id": 7,
        "technician_name": "Marco Quijano",
        "category_name": "Plumbing",
        "barangay": "Labangon",
        "document_type": "BARANGAY_CLEARANCE",
        "document_label": "Barangay Clearance",
        "file_name": "brgy_labangon_clearance_2026.jpg",
        "status": "APPROVED",
        "rejection_reason": "",
        "submitted_at": "Nov 17, 2026",
    },
    {
        "id": 203,
        "technician_id": 7,
        "technician_name": "Marco Quijano",
        "category_name": "Plumbing",
        "barangay": "Labangon",
        "document_type": "GOVERNMENT_ID",
        "document_label": "Government ID",
        "file_name": "philsys_id_quijano.png",
        "status": "REJECTED",
        "rejection_reason": "ID photo is cropped on the right edge; please re-upload a clear full-frame scan.",
        "submitted_at": "Nov 16, 2026",
    },
    {
        "id": 204,
        "technician_id": 8,
        "technician_name": "Rafael Ocampo",
        "category_name": "Electrical",
        "barangay": "Kasambagan",
        "document_type": "GOVERNMENT_ID",
        "document_label": "Government ID",
        "file_name": "drivers_license_ocampo.pdf",
        "status": "PENDING",
        "rejection_reason": "",
        "submitted_at": "Nov 18, 2026",
    },
]

DEMO_TECH_READINESS: list[dict] = [
    {
        "id": 7,
        "technician_name": "Marco Quijano",
        "category_name": "Plumbing",
        "barangay": "Labangon",
        "trade_license": "PENDING",
        "barangay_clearance": "APPROVED",
        "government_id": "REJECTED",
        "is_verified": False,
        "ready_to_verify": False,
    },
    {
        "id": 8,
        "technician_name": "Rafael Ocampo",
        "category_name": "Electrical",
        "barangay": "Kasambagan",
        "trade_license": "APPROVED",
        "barangay_clearance": "APPROVED",
        "government_id": "APPROVED",
        "is_verified": False,
        "ready_to_verify": True,
    },
    {
        "id": 1,
        "technician_name": "Mateo Villanueva",
        "category_name": "Plumbing",
        "barangay": "Lahug",
        "trade_license": "APPROVED",
        "barangay_clearance": "APPROVED",
        "government_id": "APPROVED",
        "is_verified": True,
        "ready_to_verify": True,
    },
]


def get_categories_with_counts() -> list[dict]:
    """Return service categories annotated with verified technician counts."""
    categories = []
    for cat in SERVICE_CATEGORIES:
        count = sum(
            1
            for tech in DEMO_TECHNICIANS
            if tech["category_slug"] == cat["slug"]
            and tech["is_verified"]
            and tech["is_accepting_bookings"]
        )
        categories.append({**cat, "tech_count": count})
    return categories


def filter_verified_technicians(
    query: str = "",
    category: str = "",
    barangay: str = "",
) -> list[dict]:
    """Filter verified, booking-accepting technicians by keyword, trade, and Cebu City barangay."""
    q_norm = query.strip().lower()
    cat_map = {cat["slug"]: cat for cat in SERVICE_CATEGORIES}
    results = []
    for tech in DEMO_TECHNICIANS:
        if not (tech["is_verified"] and tech["is_accepting_bookings"]):
            continue
        if category and tech["category_slug"] != category:
            continue
        if barangay and tech["barangay"] != barangay:
            continue
        if q_norm:
            cat_desc = cat_map.get(tech["category_slug"], {}).get("description", "")
            searchable = " ".join(
                [tech["full_name"], tech["category_name"], tech["bio"], cat_desc, tech["barangay"]]
            ).lower()
            if q_norm not in searchable:
                continue
        results.append(tech)
    return results


def get_technician_by_id(tech_id: int) -> dict | None:
    """Look up a technician preview entry by ID."""
    return next((tech for tech in DEMO_TECHNICIANS if tech["id"] == tech_id), None)


def get_booking_by_id(booking_id: int) -> dict | None:
    """Look up a booking preview entry by ID."""
    return next((booking for booking in DEMO_BOOKINGS if booking["id"] == booking_id), None)


def get_all_barangays() -> tuple[str, ...]:
    """Return the official 80 Cebu City barangays."""
    return CEBU_CITY_BARANGAY_NAMES
