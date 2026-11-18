"""
WSGI config for toolup project.

It exposes the WSGI callable as module-level variables ``application`` and ``app``
(the ``app`` alias is required by Vercel's ``@vercel/python`` runtime).

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "toolup.settings")

logger = logging.getLogger(__name__)


def _ensure_vercel_sqlite_ready() -> None:
    """Initialize ephemeral /tmp SQLite tables and demo accounts on Vercel cold start."""
    if not os.environ.get("VERCEL", "").strip():
        return

    from django.conf import settings
    from django.core.management import call_command

    default_db = settings.DATABASES.get("default", {})
    if default_db.get("ENGINE") != "django.db.backends.sqlite3":
        return

    try:
        call_command("migrate", interactive=False, verbosity=0)
        call_command("seed_test_accounts", verbosity=0)
    except Exception:
        logger.exception("Failed to initialize Vercel /tmp SQLite database on cold start.")


application = get_wsgi_application()
_ensure_vercel_sqlite_ready()
app = application

