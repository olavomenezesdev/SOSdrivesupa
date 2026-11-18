import unittest

from supabase_config import (
    SupabaseConfigurationError,
    get_supabase_email_redirect_url,
    get_supabase_settings,
)


class TestSupabaseConfig(unittest.TestCase):
    def test_settings_accept_project_url_and_publishable_key(self):
        settings = get_supabase_settings(
            {
                "SUPABASE_URL": " https://project.supabase.co/ ",
                "SUPABASE_ANON_KEY": "sb_publishable_test",
            }
        )

        self.assertEqual(settings.url, "https://project.supabase.co")
        self.assertEqual(settings.anon_key, "sb_publishable_test")
        self.assertIsNone(settings.service_role_key)

    def test_settings_require_valid_project_url(self):
        for url in ("", "not-a-url", "https://user:password@project.supabase.co", "https://project.supabase.co?key=x"):
            with self.subTest(url=url):
                with self.assertRaises(SupabaseConfigurationError) as error:
                    get_supabase_settings(
                        {
                            "SUPABASE_URL": url,
                            "SUPABASE_ANON_KEY": "public-key",
                        }
                    )
                self.assertEqual(error.exception.reason, "invalid_url")

    def test_settings_require_public_key(self):
        with self.assertRaises(SupabaseConfigurationError) as error:
            get_supabase_settings({"SUPABASE_URL": "https://project.supabase.co"})

        self.assertEqual(error.exception.reason, "missing_anon_key")

    def test_service_role_is_only_required_for_admin_operations(self):
        settings = get_supabase_settings(
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_ANON_KEY": "public-key",
            }
        )
        self.assertIsNone(settings.service_role_key)

        with self.assertRaises(SupabaseConfigurationError) as error:
            get_supabase_settings(
                {
                    "SUPABASE_URL": "https://project.supabase.co",
                    "SUPABASE_ANON_KEY": "public-key",
                },
                require_service_role=True,
            )

        self.assertEqual(error.exception.reason, "missing_service_role_key")

    def test_database_url_is_only_required_for_migration_operations(self):
        settings = get_supabase_settings(
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_ANON_KEY": "public-key",
            }
        )
        self.assertIsNone(settings.database_url)

        with self.assertRaises(SupabaseConfigurationError) as error:
            get_supabase_settings(
                {
                    "SUPABASE_URL": "https://project.supabase.co",
                    "SUPABASE_ANON_KEY": "public-key",
                },
                require_database=True,
            )

        self.assertEqual(error.exception.reason, "missing_database_url")

    def test_database_url_rejects_http_urls_and_mismatched_projects(self):
        for database_url in (
            "https://project.supabase.co",
            "postgresql://postgres:password@db.other-project.supabase.co:5432/postgres",
            "postgresql://postgres:password@us-east-1.pooler.supabase.com:6543/postgres",
        ):
            with self.subTest(database_url=database_url):
                with self.assertRaises(SupabaseConfigurationError) as error:
                    get_supabase_settings(
                        {
                            "SUPABASE_URL": "https://project.supabase.co",
                            "SUPABASE_ANON_KEY": "public-key",
                            "SUPABASE_DB_URL": database_url,
                        },
                        require_database=True,
                    )
                self.assertEqual(error.exception.reason, "invalid_database_url")

    def test_database_url_accepts_matching_project_and_session_pooler(self):
        settings = get_supabase_settings(
            {
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_ANON_KEY": "public-key",
                "SUPABASE_DB_URL": (
                    "postgresql://postgres.project:password@"
                    "us-east-1.pooler.supabase.com:6543/postgres"
                ),
            },
            require_database=True,
        )

        self.assertTrue(settings.database_url.startswith("postgresql://"))

    def test_email_redirect_url_requires_valid_http_url(self):
        self.assertEqual(
            get_supabase_email_redirect_url(
                {"SUPABASE_EMAIL_REDIRECT_URL": " https://app.example.com/auth/callback "}
            ),
            "https://app.example.com/auth/callback",
        )

        for redirect_url, expected_reason in (
            ("", "missing_email_redirect_url"),
            ("not-a-url", "invalid_email_redirect_url"),
            ("javascript:alert(1)", "invalid_email_redirect_url"),
            ("https://user:password@example.com/callback", "invalid_email_redirect_url"),
            ("https://example.com:invalid/callback", "invalid_email_redirect_url"),
        ):
            with self.subTest(redirect_url=redirect_url):
                with self.assertRaises(SupabaseConfigurationError) as error:
                    get_supabase_email_redirect_url(
                        {"SUPABASE_EMAIL_REDIRECT_URL": redirect_url}
                    )
                self.assertEqual(error.exception.reason, expected_reason)


if __name__ == "__main__":
    unittest.main()
