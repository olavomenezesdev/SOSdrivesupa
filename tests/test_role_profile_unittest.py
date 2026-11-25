import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from sosdrive import (
    AuthState,
    OperationalState,
    UnsupportedRoleError,
    build_image_data_url,
    format_cpf,
    format_phone,
    normalize_user_role,
    validate_signup,
)


class TestRoleProfile(unittest.TestCase):
    def test_normalize_user_role_supports_canonical_and_legacy_values(self):
        self.assertEqual(normalize_user_role("cliente"), "cliente")
        self.assertEqual(normalize_user_role("prestador"), "prestador")
        self.assertEqual(normalize_user_role("client"), "cliente")
        self.assertEqual(normalize_user_role("provider"), "prestador")

    def test_normalize_user_role_rejects_unknown_values(self):
        with self.assertRaises(UnsupportedRoleError):
            normalize_user_role("admin")

    def test_profile_masks_keep_expected_display_format(self):
        self.assertEqual(format_cpf("12345678901"), "123.456.789-01")
        self.assertEqual(format_phone("11999999999"), "(11) 99999-9999")

    def test_validate_signup_rejects_blank_values_after_trim(self):
        self.assertEqual(validate_signup("Ana", "ana@exemplo.com", "   "), "Preencha nome, email e senha para continuar.")

    def test_build_image_data_url_uses_base64_and_image_mime(self):
        data_url = build_image_data_url("avatar.png", b"\x89PNG\r\n\x1a\n")
        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        self.assertIn("iVBORw0KGgo", data_url)

    def test_load_current_user_accepts_token_when_user_id_missing(self):
        state = AuthState.__new__(AuthState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "auth_token", "valid-token")
        object.__setattr__(state, "auth_refresh_token", "valid-refresh-token")
        object.__setattr__(state, "user_id", "")
        object.__setattr__(state, "user", {})
        object.__setattr__(state, "user_json", "")
        object.__setattr__(state, "user_role", "cliente")
        object.__setattr__(state, "user_full_name", "Ana")
        object.__setattr__(state, "user_email", "ana@exemplo.com")
        object.__setattr__(state, "session_validated", False)
        restored_session = Mock(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            user={"id": "29", "email": "ana@exemplo.com", "role": "cliente"},
        )
        with patch("sosdrive.restore_supabase_session", return_value=restored_session):
            state.load_current_user()

        self.assertEqual(state.user_id, "29")
        self.assertEqual(state.user_role, "cliente")
        self.assertEqual(state.auth_refresh_token, "new-refresh-token")

    def test_customer_request_stays_searching_until_provider_accepts(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "user_vehicles", [{"id": 1, "brand": "Toyota", "model": "Corolla", "plate": "ABC-1234"}])
        object.__setattr__(state, "selected_vehicle_id", 1)
        object.__setattr__(state, "client_location", {"lat": -23.55, "lng": -46.63})
        object.__setattr__(state, "client_location_received", True)
        object.__setattr__(state, "selected_service", None)
        object.__setattr__(state, "request_status", "idle")
        object.__setattr__(state, "request_id", None)
        object.__setattr__(state, "request_server_status", "")
        object.__setattr__(state, "request_estimated_price", 0.0)
        object.__setattr__(state, "request_distance_km", 0.0)
        object.__setattr__(state, "request_error_message", "")
        object.__setattr__(state, "show_profile_link", False)
        object.__setattr__(state, "pending_service_type", "")

        object.__setattr__(state, "_get_auth_token", AsyncMock(return_value="token-123"))
        with patch(
            "sosdrive.create_service_request_supabase",
            return_value={
                "request_id": 99,
                "status": "pending",
                "estimated_price": 150.0,
                "distance_km": 4.4,
            },
        ) as create_request:
            asyncio.run(state._submit_customer_request("tire"))

        create_request.assert_called_once_with(
            "token-123",
            "tire",
            1,
            -23.55,
            -46.63,
        )
        self.assertEqual(state.request_status, "searching")
        self.assertEqual(state.request_id, 99)

    def test_customer_request_accepts_zero_coordinates_when_geolocation_is_set(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "user_vehicles": [{"id": 1}],
            "selected_vehicle_id": 1,
            "client_location": {"lat": 0.0, "lng": 0.0},
            "client_location_received": True,
            "request_status": "idle",
            "request_error_message": "",
            "show_profile_link": False,
            "selected_service": None,
            "request_id": None,
            "request_server_status": "",
            "request_estimated_price": 0.0,
            "request_distance_km": 0.0,
        }.items():
            object.__setattr__(state, name, value)
        object.__setattr__(state, "_get_auth_token", AsyncMock(return_value="token-123"))

        with patch(
            "sosdrive.create_service_request_supabase",
            return_value={"request_id": 101, "status": "pending"},
        ) as create_request:
            asyncio.run(state._submit_customer_request("battery"))

        create_request.assert_called_once_with("token-123", "battery", 1, 0.0, 0.0)
        self.assertEqual(state.request_status, "searching")
        self.assertEqual(state.request_id, 101)

if __name__ == "__main__":
    unittest.main()
