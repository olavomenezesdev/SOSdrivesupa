import unittest
from unittest.mock import patch

from scripts.apply_supabase_migrations import apply_migrations, migration_files


class TestSupabaseMigrations(unittest.TestCase):
    def test_migration_files_are_sorted_and_present(self):
        files = migration_files()

        self.assertGreater(len(files), 0)
        self.assertEqual(files, sorted(files))

    def test_listing_migrations_does_not_connect_to_the_database(self):
        with patch(
            "scripts.apply_supabase_migrations.psycopg.connect",
            side_effect=AssertionError("listing migrations must not connect"),
        ):
            migrations = apply_migrations(apply=False)

        self.assertEqual(
            migrations,
            [path.name for path in migration_files()],
        )

    def test_provider_earnings_migration_is_confirmed_and_idempotent(self):
        migration = next(
            path
            for path in migration_files()
            if path.name == "20261123100000_provider_earnings.sql"
        )
        sql = migration.read_text(encoding="utf-8").lower()

        self.assertIn("create table public.provider_earnings", sql)
        self.assertIn("service_request_id bigint not null unique", sql)
        self.assertIn("payment_id bigint not null unique", sql)
        self.assertIn("after insert or update of status", sql)
        self.assertIn("if new.status <> 'confirmed' then", sql)
        self.assertIn("on conflict (service_request_id) do nothing", sql)
        self.assertIn("payment.status = 'confirmed'", sql)
        self.assertIn("revoke all on public.provider_earnings from anon, authenticated", sql)


if __name__ == "__main__":
    unittest.main()
