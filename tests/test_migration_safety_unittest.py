import unittest

from migration_safety import sanitize_event_metadata


class TestMigrationSafety(unittest.TestCase):
    def test_sanitizes_sensitive_metadata_keys_recursively(self):
        metadata = {
            "action": "login",
            "user": {
                "id": 12,
                "email": "demo@example.test",
                "password": "must-not-survive",
                "password_hash": "must-not-survive",
                "nested": [
                    {"refresh_token": "must-not-survive", "display_name": "Demo"},
                    {"service_secret": "must-not-survive", "count": 3},
                ],
            },
            "request": {
                "authorization": "must-not-survive",
                "event_hash": "must-not-survive",
                "service": "tire",
            },
        }

        sanitized = sanitize_event_metadata(metadata)

        self.assertEqual(sanitized["action"], "login")
        self.assertEqual(sanitized["user"]["id"], 12)
        self.assertEqual(sanitized["user"]["email"], "demo@example.test")
        self.assertEqual(sanitized["user"]["nested"][0], {"display_name": "Demo"})
        self.assertEqual(sanitized["user"]["nested"][1], {"count": 3})
        self.assertEqual(sanitized["request"], {"service": "tire"})

    def test_preserves_non_secret_values_and_does_not_mutate_input(self):
        metadata = {"attempt": 3, "flags": [True, None], "password_reset": {"token": "secret"}}

        sanitized = sanitize_event_metadata(metadata)

        self.assertEqual(sanitized, {"attempt": 3, "flags": [True, None]})
        self.assertIn("password_reset", metadata)

    def test_handles_nested_tuples(self):
        self.assertEqual(
            sanitize_event_metadata(({"api_key": "secret", "safe": "value"},)),
            ({"safe": "value"},),
        )


if __name__ == "__main__":
    unittest.main()
