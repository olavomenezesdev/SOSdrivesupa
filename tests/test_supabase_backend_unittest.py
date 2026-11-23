import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from supabase_config import SupabaseSettings
from supabase_backend import (
    SupabaseAuthenticationError,
    SupabaseBackendError,
    SupabaseConfigurationRuntimeError,
    _status,
    fetch_service_messages,
    resend_signup_confirmation,
    send_service_message,
    sign_in,
    sign_up,
    start_service_request,
)


class TestSupabaseBackend(unittest.TestCase):
    def test_database_error_codes_map_to_http_semantics(self):
        cases = (
            ("PGRST301", 401),
            ("42501", 403),
            ("40001", 409),
            ("22023", 400),
            ("23505", 409),
            ("unknown", 500),
        )
        for code, expected_status in cases:
            with self.subTest(code=code):
                error = RuntimeError(code)
                error.code = code
                self.assertEqual(_status(error), expected_status)
        self.assertEqual(_status(httpx.ReadTimeout("timeout")), 504)
        self.assertEqual(_status(httpx.ConnectError("connection failed")), 503)

    def test_sign_in_loads_role_profile_using_the_authenticated_jwt(self):
        auth_user = SimpleNamespace(
            id="auth-user-uuid",
            email="ana@example.com",
            user_metadata={"name": "Ana"},
        )
        auth_client = Mock()
        auth_client.auth.sign_in_with_password.return_value = SimpleNamespace(
            session=SimpleNamespace(
                access_token="access-token",
                refresh_token="refresh-token",
                user=auth_user,
            ),
            user=auth_user,
        )
        profile_client = Mock()
        profile_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "auth-user-uuid",
                "role": "cliente",
                "full_name": "Ana Silva",
                "cpf": "",
                "telefone": "",
                "foto_perfil": "",
            }
        ]

        with patch("supabase_backend._client", side_effect=[auth_client, profile_client]):
            session = sign_in(" ANA@EXAMPLE.COM ", "secret")

        auth_client.auth.sign_in_with_password.assert_called_once_with(
            {"email": "ana@example.com", "password": "secret"}
        )
        profile_client.postgrest.auth.assert_called_once_with("access-token")
        self.assertEqual(session.access_token, "access-token")
        self.assertEqual(session.refresh_token, "refresh-token")
        self.assertEqual(session.user["id"], "auth-user-uuid")
        self.assertEqual(session.user["role"], "cliente")
        self.assertEqual(session.user["name"], "Ana Silva")

    def test_sign_in_closes_http_clients_after_loading_the_profile(self):
        auth_user = SimpleNamespace(
            id="auth-user-uuid",
            email="ana@example.com",
            user_metadata={},
        )
        auth_client = Mock()
        auth_client._postgrest = auth_client.postgrest
        auth_client._storage = None
        auth_client._functions = None
        auth_client.auth.sign_in_with_password.return_value = SimpleNamespace(
            session=SimpleNamespace(
                access_token="access-token",
                refresh_token="refresh-token",
                user=auth_user,
            ),
            user=auth_user,
        )
        profile_client = Mock()
        profile_client._postgrest = profile_client.postgrest
        profile_client._storage = None
        profile_client._functions = None
        profile_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "auth-user-uuid",
                "role": "cliente",
                "full_name": "Ana Silva",
                "cpf": "",
                "telefone": "",
                "foto_perfil": "",
            }
        ]

        with (
            patch(
                "supabase_backend._settings",
                return_value=SupabaseSettings(
                    url="https://example.supabase.co",
                    anon_key="anon",
                ),
            ),
            patch(
                "supabase_backend.create_client",
                side_effect=[auth_client, profile_client],
            ),
        ):
            sign_in("ana@example.com", "secret")

        for client in (auth_client, profile_client):
            client.auth.close.assert_called_once_with()
            client.postgrest.aclose.assert_called_once_with()

    def test_sign_up_supports_email_confirmation_without_a_session(self):
        client = Mock()
        client.auth.sign_up.return_value = SimpleNamespace(session=None, user=None)
        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                return_value="https://app.example.com/auth/callback",
            ),
        ):
            result = sign_up("ana@example.com", "secret", " Ana ", "cliente")

        self.assertIsNone(result)
        client.auth.sign_up.assert_called_once_with(
            {
                "email": "ana@example.com",
                "password": "secret",
                "options": {
                    "data": {"name": "Ana", "role": "cliente"},
                    "email_redirect_to": "https://app.example.com/auth/callback",
                },
            }
        )

    def test_sign_up_requires_configured_redirect_url(self):
        client = Mock()
        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                side_effect=SupabaseConfigurationRuntimeError(
                    503,
                    "Email confirmation redirect is not configured",
                ),
            ),
            self.assertRaises(SupabaseConfigurationRuntimeError),
        ):
            sign_up("ana@example.com", "secret", "Ana", "cliente")
        client.auth.sign_up.assert_not_called()

    def test_resend_confirmation_uses_email_redirect_and_no_extra_request(self):
        client = Mock()
        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                return_value="https://app.example.com/auth/callback",
            ),
        ):
            resend_signup_confirmation(" ANA@EXAMPLE.COM ")

        client.auth.resend.assert_called_once_with(
            {
                "type": "signup",
                "email": "ana@example.com",
                "options": {"email_redirect_to": "https://app.example.com/auth/callback"},
            }
        )

    def test_resend_confirmation_preserves_429_without_raw_response(self):
        client = Mock()
        error = RuntimeError("private response content")
        error.status_code = 429
        client.auth.resend.side_effect = error

        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                return_value="https://app.example.com/auth/callback",
            ),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            resend_signup_confirmation("ana@example.com")

        self.assertEqual(raised.exception.status_code, 429)
        self.assertNotIn("private response", str(raised.exception))
        client.auth.resend.assert_called_once()

    def test_sign_up_sanitizes_bad_request_details(self):
        client = Mock()
        error = RuntimeError("private email and password payload")
        error.status_code = 400
        client.auth.sign_up.side_effect = error

        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                return_value="https://app.example.com/auth/callback",
            ),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            sign_up("ana@example.com", "secret", "Ana", "cliente")

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.message,
            "Supabase rejected the signup data or Auth configuration",
        )
        self.assertNotIn("private email", str(raised.exception))

    def test_sign_up_maps_duplicate_email_code_to_conflict(self):
        client = Mock()
        error = RuntimeError("sensitive duplicate-account response")
        error.status_code = 400
        error.code = "user_already_exists"
        client.auth.sign_up.side_effect = error

        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                return_value="https://app.example.com/auth/callback",
            ),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            sign_up("ana@example.com", "secret", "Ana", "cliente")

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.message, "This email is already registered")
        self.assertNotIn("sensitive duplicate", str(raised.exception))

    def test_sign_up_preserves_rate_limit_status_without_raw_response(self):
        client = Mock()
        error = RuntimeError("sensitive response content")
        error.status_code = 429
        client.auth.sign_up.side_effect = error

        with (
            patch("supabase_backend._client", return_value=client),
            patch(
                "supabase_backend._email_redirect_to",
                return_value="https://app.example.com/auth/callback",
            ),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            sign_up("ana@example.com", "secret", "Ana", "cliente")

        self.assertEqual(raised.exception.status_code, 429)
        self.assertNotIn("sensitive response content", str(raised.exception))

    def test_sign_in_identifies_unconfirmed_email_with_safe_message(self):
        client = Mock()
        error = RuntimeError("raw auth response")
        error.status_code = 400
        error.code = "email_not_confirmed"
        client.auth.sign_in_with_password.side_effect = error

        with (
            patch("supabase_backend._client", return_value=client),
            self.assertRaises(SupabaseAuthenticationError) as raised,
        ):
            sign_in("ana@example.com", "secret")

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.message,
            "Email confirmation is still enabled in Supabase Auth",
        )
        self.assertNotIn("raw auth response", str(raised.exception))

    def test_sign_in_rejects_auth_user_without_profile(self):
        auth_user = SimpleNamespace(id="auth-user-uuid", email="ana@example.com", user_metadata={})
        auth_client = Mock()
        auth_client.auth.sign_in_with_password.return_value = SimpleNamespace(
            session=SimpleNamespace(
                access_token="access-token",
                refresh_token="refresh-token",
                user=auth_user,
            ),
            user=auth_user,
        )
        profile_client = Mock()
        profile_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

        with (
            patch("supabase_backend._client", side_effect=[auth_client, profile_client]),
            self.assertRaises(SupabaseAuthenticationError),
        ):
            sign_in("ana@example.com", "secret")

    def test_fetch_messages_filters_to_request_and_orders_oldest_first(self):
        client = Mock()
        query = client.table.return_value.select.return_value
        query.eq.return_value.order.return_value.execute.return_value.data = [
            {"id": 1, "service_request_id": 42, "message_text": "Oi"}
        ]

        with patch("supabase_backend._authenticated_client", return_value=client):
            messages = fetch_service_messages("client-token", 42)

        client.table.assert_called_once_with("service_messages")
        query.eq.assert_called_once_with("service_request_id", 42)
        query.eq.return_value.order.assert_called_once_with("created_at")
        self.assertEqual(messages[0]["id"], 1)

    def test_message_sender_is_derived_from_authenticated_user(self):
        client = Mock()
        client.auth.get_user.return_value = SimpleNamespace(
            user=SimpleNamespace(id="auth-user-uuid")
        )
        query = client.table.return_value
        query.insert.return_value.execute.return_value.data = [
            {
                "id": 7,
                "service_request_id": 42,
                "sender_id": "auth-user-uuid",
                "message_text": "Olá",
            }
        ]

        with patch("supabase_backend._authenticated_client", return_value=client):
            message = send_service_message("access-token", 42, " Olá ")

        query.insert.assert_called_once_with(
            {
                "service_request_id": 42,
                "sender_id": "auth-user-uuid",
                "message_text": "Olá",
            }
        )
        self.assertEqual(message["sender_id"], "auth-user-uuid")

    def test_start_service_request_calls_authenticated_rpc_and_returns_in_progress_row(self):
        client = Mock()
        request = {"id": 42, "provider_id": "provider-uuid", "status": "in_progress"}
        client.rpc.return_value.execute.return_value.data = [request]

        with patch("supabase_backend._authenticated_client", return_value=client):
            result = start_service_request("provider-token", 42)

        client.rpc.assert_called_once_with(
            "start_service_request",
            {"p_request_id": 42},
        )
        self.assertEqual(result, request)

    def test_start_service_request_rejects_unexpected_status(self):
        client = Mock()
        client.rpc.return_value.execute.return_value.data = [
            {"id": 42, "status": "accepted"}
        ]

        with (
            patch("supabase_backend._authenticated_client", return_value=client),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            start_service_request("provider-token", 42)

        self.assertEqual(raised.exception.status_code, 502)

    def test_start_service_request_surfaces_authorization_errors(self):
        client = Mock()
        error = RuntimeError("private database response")
        error.code = "42501"
        client.rpc.side_effect = error

        with (
            patch("supabase_backend._authenticated_client", return_value=client),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            start_service_request("provider-token", 42)

        self.assertEqual(raised.exception.status_code, 403)
        self.assertNotIn("private database response", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
