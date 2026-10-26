import asyncio
import unittest
from unittest.mock import patch

from sosdrive import (
    AuthState,
    SupabaseAuthenticationError,
    SupabaseBackendError,
    SupabaseConfigurationRuntimeError,
    SupabaseSession,
)


def make_auth_state(email="ana@example.com", password="secret"):
    state = AuthState.__new__(AuthState)
    object.__setattr__(state, "dirty_vars", set())
    values = {
        "auth_token": "",
        "auth_refresh_token": "",
        "user_json": "",
        "user": {},
        "user_id": "",
        "user_role": "cliente",
        "email": email,
        "password": password,
        "error_message": "",
        "is_loading": False,
        "session_validated": False,
        "user_profile_photo": "",
        "user_profile_photo_path": "",
        "selected_profile_image": "",
        "selected_profile_filename": "",
        "selected_profile_uploaded_url": "",
        "user_full_name": "Usuário SOS",
        "user_email": "usuario@exemplo.com",
        "user_phone": "(11) 99999-9999",
        "user_cpf": "",
        "profile_exists": False,
        "signup_name": "Ana Silva",
        "signup_email": email,
        "signup_password": password,
        "signup_role": "cliente",
        "signup_message": "",
        "pending_confirmation_email": "",
        "resend_message": "",
        "resend_cooldown_until": 0,
        "is_resending_confirmation": False,
    }
    for name, value in values.items():
        object.__setattr__(state, name, value)
    return state


def consume_event_generator(generator):
    async def consume():
        return [event async for event in generator]

    return asyncio.run(consume())


class TestSupabaseLogin(unittest.TestCase):
    def make_session(self, role="cliente"):
        return SupabaseSession(
            access_token="access-token",
            refresh_token="refresh-token",
            user={
                "id": "auth-user-uuid",
                "email": "ana@example.com",
                "name": "Ana Silva",
                "role": role,
            },
        )

    def test_login_routes_client_and_provider_and_keeps_tokens_in_server_state(self):
        for role, expected_route in (
            ("cliente", "/perfil-cliente"),
            ("prestador", "/perfil-prestador"),
        ):
            with self.subTest(role=role):
                state = make_auth_state()
                with patch("sosdrive.sign_in_supabase", return_value=self.make_session(role)):
                    events = consume_event_generator(state.login())

                self.assertEqual(state.auth_token, "access-token")
                self.assertEqual(state.auth_refresh_token, "refresh-token")
                self.assertEqual(state.user_id, "auth-user-uuid")
                self.assertEqual(state.user_role, role)
                self.assertFalse(state.is_loading)
                self.assertEqual(state.password, "")
                self.assertEqual(len(events), 2)
                self.assertIn(expected_route, repr(events[-1]))
                self.assertEqual(AuthState.__annotations__["auth_token"], "str")

    def test_login_maps_invalid_credentials_to_safe_message(self):
        state = make_auth_state()
        with patch(
            "sosdrive.sign_in_supabase",
            side_effect=SupabaseAuthenticationError(401, "sensitive backend details"),
        ):
            consume_event_generator(state.login())

        self.assertEqual(state.error_message, "E-mail ou senha incorretos.")
        self.assertEqual(state.password, "")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.auth_token, "")
        self.assertNotIn("sensitive backend details", state.error_message)

    def test_login_does_not_redirect_for_unsupported_role(self):
        state = make_auth_state()
        with patch("sosdrive.sign_in_supabase", return_value=self.make_session("admin")):
            events = consume_event_generator(state.login())

        self.assertEqual(events, [None])
        self.assertEqual(state.error_message, "Sua conta não possui um tipo de usuário válido.")
        self.assertEqual(state.auth_token, "")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.password, "")

    def test_login_requires_valid_supabase_configuration_without_network(self):
        state = make_auth_state()
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("sosdrive.sign_in_supabase", side_effect=RuntimeError("Supabase is not configured")),
        ):
            consume_event_generator(state.login())

        self.assertIn("Supabase", state.error_message)
        self.assertEqual(state.password, "")
        self.assertFalse(state.is_loading)

    def test_signup_without_session_shows_confirmation_message(self):
        state = make_auth_state()
        with patch("sosdrive.sign_up_supabase", return_value=None) as sign_up:
            events = consume_event_generator(state.signup())

        sign_up.assert_called_once_with("ana@example.com", "secret", "Ana Silva", "cliente")
        self.assertEqual(events, [None])
        self.assertEqual(
            state.signup_message,
            "Enviamos um e-mail de confirmação para ana@example.com. "
            "Confirme para entrar. Olhe também a caixa de spam.",
        )
        self.assertEqual(state.error_message, "")
        self.assertEqual(state.signup_name, "Ana Silva")
        self.assertEqual(state.signup_email, "ana@example.com")
        self.assertEqual(state.pending_confirmation_email, "ana@example.com")
        self.assertEqual(state.auth_token, "")
        self.assertEqual(state.signup_password, "")
        self.assertFalse(state.is_loading)

    def test_signup_does_not_authenticate_when_confirmation_is_disabled(self):
        state = make_auth_state()
        session = self.make_session("prestador")
        with patch("sosdrive.sign_up_supabase", return_value=session):
            events = consume_event_generator(state.signup())

        self.assertEqual(state.auth_token, "")
        self.assertEqual(state.auth_refresh_token, "")
        self.assertEqual(state.user_role, "cliente")
        self.assertEqual(state.email, "ana@example.com")
        self.assertEqual(events, [None])
        self.assertIn("sem exigir confirmação", state.error_message)
        self.assertEqual(state.signup_message, "")
        self.assertEqual(state.pending_confirmation_email, "")
        self.assertEqual(state.signup_password, "")
        self.assertFalse(state.is_loading)

    def test_signup_rate_limit_shows_retry_guidance_without_backend_details(self):
        state = make_auth_state()
        with patch(
            "sosdrive.sign_up_supabase",
            side_effect=SupabaseBackendError(429, "sensitive backend details"),
        ) as sign_up:
            consume_event_generator(state.signup())

        sign_up.assert_called_once()
        self.assertEqual(
            state.error_message,
            "Muitas tentativas. Aguarde alguns minutos e tente novamente.",
        )
        self.assertNotIn("sensitive backend details", state.error_message)
        self.assertEqual(state.signup_password, "")
        self.assertFalse(state.is_loading)

    def test_signup_blocks_duplicate_submission_while_request_is_pending(self):
        state = make_auth_state()
        calls = []

        async def run_test():
            started = asyncio.Event()
            release = asyncio.Event()

            async def blocking_to_thread(*args):
                calls.append(args)
                started.set()
                await release.wait()
                return None

            async def invoke_signup():
                async for _ in state.signup():
                    pass

            with patch("sosdrive.asyncio.to_thread", side_effect=blocking_to_thread):
                first_request = asyncio.create_task(invoke_signup())
                await started.wait()
                await invoke_signup()
                self.assertEqual(len(calls), 1)
                release.set()
                await first_request

        asyncio.run(run_test())
        self.assertEqual(len(calls), 1)
        self.assertFalse(state.is_loading)
        self.assertEqual(state.signup_password, "")

    def test_resend_confirmation_has_60_second_cooldown_and_releases_after_expiry(self):
        state = make_auth_state()
        state.pending_confirmation_email = "ana@example.com"
        calls = []

        async def fake_to_thread(*args):
            calls.append(args)

        async def run_test():
            with (
                patch("sosdrive.asyncio.to_thread", side_effect=fake_to_thread),
                patch("sosdrive.time.time", return_value=1_000),
            ):
                async for _ in state.resend_confirmation_email():
                    pass
                self.assertEqual(state.resend_cooldown_until, 1_060)
                self.assertEqual(state.resend_seconds_remaining, 60)
                self.assertEqual(len(calls), 1)
                async for _ in state.resend_confirmation_email():
                    pass
                self.assertEqual(len(calls), 1)

            with (
                patch("sosdrive.asyncio.to_thread", side_effect=fake_to_thread),
                patch("sosdrive.time.time", return_value=1_060),
            ):
                async for _ in state.resend_confirmation_email():
                    pass
                self.assertEqual(len(calls), 2)
                self.assertEqual(state.resend_seconds_remaining, 60)

        asyncio.run(run_test())
        self.assertEqual(state.resend_message, "E-mail de confirmação reenviado. Confira também a caixa de spam.")
        self.assertFalse(state.is_resending_confirmation)

    def test_resend_confirmation_rate_limit_is_sanitized_and_starts_cooldown(self):
        state = make_auth_state()
        state.pending_confirmation_email = "ana@example.com"
        with (
            patch(
                "sosdrive.resend_signup_confirmation_supabase",
                side_effect=SupabaseBackendError(429, "sensitive backend details"),
            ) as resend,
            patch("sosdrive.time.time", return_value=2_000),
        ):
            consume_event_generator(state.resend_confirmation_email())

        resend.assert_called_once_with("ana@example.com")
        self.assertEqual(
            state.resend_message,
            "Muitas tentativas. Aguarde alguns minutos e tente novamente.",
        )
        self.assertEqual(state.resend_cooldown_until, 2_060)
        self.assertNotIn("sensitive backend details", state.resend_message)
        self.assertFalse(state.is_resending_confirmation)

    def test_signup_bad_request_shows_actionable_safe_guidance(self):
        state = make_auth_state()
        with patch(
            "sosdrive.sign_up_supabase",
            side_effect=SupabaseBackendError(400, "private payload"),
        ):
            consume_event_generator(state.signup())

        self.assertIn("HTTP 400", state.error_message)
        self.assertIn("senha", state.error_message)
        self.assertNotIn("private payload", state.error_message)
        self.assertFalse(state.is_loading)

    def test_signup_reports_missing_confirmation_redirect_configuration(self):
        state = make_auth_state()
        with patch(
            "sosdrive.sign_up_supabase",
            side_effect=SupabaseConfigurationRuntimeError(
                503,
                "private configuration detail",
            ),
        ) as sign_up:
            consume_event_generator(state.signup())

        sign_up.assert_called_once()
        self.assertEqual(
            state.error_message,
            "O destino de confirmação não está configurado corretamente neste ambiente.",
        )
        self.assertNotIn("private configuration detail", state.error_message)
        self.assertEqual(state.signup_password, "")
        self.assertFalse(state.is_loading)

    def test_login_reports_unconfirmed_email_and_enables_resend(self):
        state = make_auth_state()
        with patch(
            "sosdrive.sign_in_supabase",
            side_effect=SupabaseAuthenticationError(
                400,
                "Email confirmation is still enabled in Supabase Auth",
            ),
        ):
            consume_event_generator(state.login())

        self.assertIn("não foi confirmado", state.error_message)
        self.assertNotIn("incorretos", state.error_message)
        self.assertEqual(state.pending_confirmation_email, "ana@example.com")
        self.assertFalse(state.is_loading)


if __name__ == "__main__":
    unittest.main()
