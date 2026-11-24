"""Apply versioned SQL migrations to the configured Supabase project."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg

from supabase_config import SupabaseConfigurationError, get_supabase_settings


MIGRATIONS_DIR = PROJECT_ROOT / "supabase" / "migrations"
TARGET_TABLES = (
    "profiles",
    "vehicles",
    "service_requests",
    "service_request_acceptance",
    "service_messages",
    "event_log",
    "service_request_payments",
    "service_request_reviews",
    "provider_earnings",
)


def migration_files() -> list[Path]:
    """Return migrations in deterministic version order."""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def apply_migrations(*, apply: bool) -> list[str]:
    """Validate the target and apply pending migrations transactionally."""
    files = migration_files()
    if not files:
        raise RuntimeError("No SQL migrations were found")
    if not apply:
        return [path.name for path in files]

    settings = get_supabase_settings(require_database=True)
    if settings.database_url is None:
        raise SupabaseConfigurationError("missing_database_url")

    with psycopg.connect(settings.database_url, connect_timeout=15) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select pg_advisory_lock(hashtext(%s))", ("sosdrive-schema-migrations",))
            try:
                cursor.execute("create schema if not exists private")
                cursor.execute(
                    """
                    create table if not exists private.schema_migrations (
                        version text primary key,
                        applied_at timestamptz not null default now()
                    )
                    """
                )
                cursor.execute("select exists (select 1 from private.schema_migrations)")
                has_applied_migrations = cursor.fetchone()[0]

                applied: list[str] = []
                for migration in files:
                    cursor.execute(
                        "select exists (select 1 from private.schema_migrations where version = %s)",
                        (migration.name,),
                    )
                    if cursor.fetchone()[0]:
                        continue

                    if not has_applied_migrations:
                        cursor.execute(
                            """
                            select count(*)
                            from information_schema.tables
                            where table_schema = 'public'
                              and table_name = any(%s)
                            """,
                            (list(TARGET_TABLES),),
                        )
                        existing_table_count = cursor.fetchone()[0]
                        if existing_table_count:
                            raise RuntimeError(
                                "Refusing to apply the initial migration because SOS Drive tables already exist"
                            )

                    cursor.execute(migration.read_text(encoding="utf-8"))
                    cursor.execute(
                        "insert into private.schema_migrations (version) values (%s)",
                        (migration.name,),
                    )
                    has_applied_migrations = True
                    applied.append(migration.name)

                cursor.execute("select pg_advisory_unlock(hashtext(%s))", ("sosdrive-schema-migrations",))
                return applied
            except Exception:
                connection.rollback()
                raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply pending migrations. Without this flag, only list migration files.",
    )
    args = parser.parse_args()

    try:
        migrations = apply_migrations(apply=args.apply)
    except SupabaseConfigurationError as error:
        print(f"Supabase configuration error: {error.reason}")
        return 2
    except Exception as error:
        print(f"Migration failed: {type(error).__name__}; database changes were rolled back.")
        return 1

    if not args.apply:
        print("Available migrations:")
        for migration in migrations:
            print(f"- {migration}")
    elif migrations:
        print("Applied migrations:")
        for migration in migrations:
            print(f"- {migration}")
    else:
        print("No pending migrations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
