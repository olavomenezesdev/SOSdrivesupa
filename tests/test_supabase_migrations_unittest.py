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


if __name__ == "__main__":
    unittest.main()
