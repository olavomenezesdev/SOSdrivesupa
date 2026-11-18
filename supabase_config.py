"""Backend-only configuration for Supabase integrations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict
from psycopg.errors import ProgrammingError


load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=False)


class SupabaseConfigurationError(RuntimeError):
    """Raised when required Supabase configuration is missing or invalid."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class SupabaseSettings:
    """Validated Supabase settings; the service key is reserved for admin tooling."""

    url: str
    anon_key: str
    service_role_key: str | None = None
    database_url: str | None = None


def get_supabase_settings(
    environ: Mapping[str, str] | None = None,
    *,
    require_service_role: bool = False,
    require_database: bool = False,
) -> SupabaseSettings:
    """Load and validate Supabase credentials without logging their values."""
    source = os.environ if environ is None else environ
    url = source.get("SUPABASE_URL", "").strip().rstrip("/")
    anon_key = source.get("SUPABASE_ANON_KEY", "").strip()
    service_role_key = source.get("SUPABASE_SERVICE_ROLE_KEY", "").strip() or None
    database_url = source.get("SUPABASE_DB_URL", "").strip() or None

    try:
        parsed_url = urlsplit(url)
        valid_url = (
            parsed_url.scheme in {"http", "https"}
            and bool(parsed_url.hostname)
            and parsed_url.username is None
            and parsed_url.password is None
            and parsed_url.query == ""
            and parsed_url.fragment == ""
        )
    except ValueError:
        valid_url = False

    if not valid_url:
        raise SupabaseConfigurationError("invalid_url")
    if not anon_key:
        raise SupabaseConfigurationError("missing_anon_key")
    if require_service_role and not service_role_key:
        raise SupabaseConfigurationError("missing_service_role_key")
    if require_database:
        if not database_url:
            raise SupabaseConfigurationError("missing_database_url")
        try:
            database_info = conninfo_to_dict(database_url)
        except (ProgrammingError, ValueError):
            raise SupabaseConfigurationError("invalid_database_url") from None
        if not (
            database_url.startswith("postgresql://")
            or database_url.startswith("postgres://")
        ):
            raise SupabaseConfigurationError("invalid_database_url")
        database_host = (database_info.get("host") or "").lower()
        database_user = database_info.get("user") or ""
        project_ref = parsed_url.hostname.split(".", 1)[0].lower()
        is_project_database = (
            database_host == f"db.{project_ref}.supabase.co"
            or (
                database_host.endswith(".pooler.supabase.com")
                and project_ref in database_user.lower()
            )
        )
        if not is_project_database:
            raise SupabaseConfigurationError("invalid_database_url")

    return SupabaseSettings(
        url=url,
        anon_key=anon_key,
        service_role_key=service_role_key,
        database_url=database_url,
    )


def get_supabase_email_redirect_url(
    environ: Mapping[str, str] | None = None,
) -> str:
    """Return a validated confirmation redirect URL without logging its value."""
    source = os.environ if environ is None else environ
    redirect_url = source.get("SUPABASE_EMAIL_REDIRECT_URL", "").strip()
    if not redirect_url:
        raise SupabaseConfigurationError("missing_email_redirect_url")

    try:
        parsed_url = urlsplit(redirect_url)
        valid_url = (
            parsed_url.scheme in {"http", "https"}
            and bool(parsed_url.hostname)
            and parsed_url.username is None
            and parsed_url.password is None
            and parsed_url.port != 0
            and not any(character.isspace() for character in redirect_url)
        )
    except ValueError:
        valid_url = False
    if not valid_url:
        raise SupabaseConfigurationError("invalid_email_redirect_url")
    return redirect_url
