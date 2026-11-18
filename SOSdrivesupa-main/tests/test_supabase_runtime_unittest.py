import asyncio
import inspect
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import requests

from supabase_backend import SupabaseBackendError
from sosdrive import (
    AuthState,
    OperationalState,
    _load_project_environment,
    profile_screen,
    provider_home_screen,
    user_home_screen,
)


class TestSupabaseRuntime(unittest.TestCase):
    def render_component(self, component):
        return re.sub(
            r"\\u([0-9a-fA-F]{4})",
            lambda match: chr(int(match.group(1), 16)),
            str(component),
        )

    def test_provider_home_renders_empty_loading_error_and_retry_feedback(self):
        rendered = self.render_component(provider_home_screen())

        self.assertIn("Nenhum chamado ou cliente próximo no momento", rendered)
        self.assertIn("Carregando chamados próximos...", rendered)
        self.assertIn("pending_requests_error_rx_state_", rendered)
        self.assertIn("Tentar novamente", rendered)
        self.assertIn("Solicitações Próximas", rendered)

    def test_client_home_explains_no_active_call_and_keeps_request_action(self):
        rendered = self.render_component(user_home_screen())

        self.assertIn("Você ainda não tem um chamado em andamento. Solicite socorro quando precisar.", rendered)
        self.assertIn("Solicitar Socorro", rendered)
        self.assertIn("Chamado em andamento", rendered)

    def test_profile_return_routes_to_role_specific_home(self):
        rendered = self.render_component(profile_screen())

        self.assertIn("/home_provider", rendered)
        self.assertIn("/home_client", rendered)
        self.assertIn("Voltar", rendered)
        self.assertIn("Sair", rendered)

    def test_profile_hides_vehicle_ui_for_providers_and_keeps_save_action(self):
        rendered = self.render_component(profile_screen())
        provider_condition = 'user_role_rx_state_?.valueOf?.() === "prestador"'

        checklist_start = rendered.index('className:"rx-Stack profile-checklist"')
        info_start = rendered.index('className:"rx-Stack profile-info-section"', checklist_start)
        checklist = rendered[checklist_start:info_start]
        self.assertIn(provider_condition, checklist)
        self.assertIn("Cadastre seu veículo", checklist)

        vehicles_start = rendered.index('className:"rx-Stack profile-vehicles-section"')
        save_start = rendered.index('className:"profile-save-button"', vehicles_start)
        vehicles = rendered[vehicles_start:save_start]
        self.assertEqual(vehicles.count(provider_condition), 2)
        self.assertIn("profile-vehicles-header", vehicles)
        self.assertIn("profile-vehicle-list", vehicles)
        self.assertIn("profile-save-button", rendered[vehicles_start:])
        self.assertIn("auth_state.save_profile", rendered[vehicles_start:])
        self.assertIn("profile_is_loading_rx_state_", rendered[vehicles_start:])

    def test_profile_completion_tracks_fields_and_registered_vehicle(self):
        state = AuthState.__new__(AuthState)
        for name, value in {
            "user_full_name": "Usuário SOS",
            "user_cpf": "",
            "user_phone": "(11) 99999-9999",
            "selected_profile_image": "",
            "user_profile_photo": "",
        }.items():
            object.__setattr__(state, name, value)

        self.assertEqual(state.profile_completed_fields, 0)
        self.assertFalse(state.profile_has_name)
        self.assertFalse(state.profile_has_valid_phone)

        complete_state = AuthState.__new__(AuthState)
        for name, value in {
            "user_full_name": "Bruno Alves",
            "user_cpf": "123.456.789-01",
            "user_phone": "(11) 91234-5678",
            "selected_profile_image": "data:image/png;base64,abc",
        }.items():
            object.__setattr__(complete_state, name, value)

        self.assertEqual(complete_state.profile_completed_fields, 4)
        self.assertTrue(complete_state.profile_has_name)
        self.assertTrue(complete_state.profile_has_valid_cpf)
        self.assertTrue(complete_state.profile_has_valid_phone)
        self.assertTrue(complete_state.profile_has_photo)

        empty_vehicles = OperationalState.__new__(OperationalState)
        object.__setattr__(empty_vehicles, "user_vehicles", [])
        self.assertFalse(empty_vehicles.has_profile_vehicles)
        registered_vehicles = OperationalState.__new__(OperationalState)
        object.__setattr__(registered_vehicles, "user_vehicles", [{"id": 1}])
        self.assertTrue(registered_vehicles.has_profile_vehicles)

    def test_provider_home_loads_requests_and_clears_loading_state(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "pending_requests_loading": False,
            "pending_requests_error": "",
            "available_requests": [],
            "current_provider_id": 1,
            "provider_locations": {},
            "providers": [],
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.load_pending_requests()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch(
                "sosdrive.fetch_pending_requests_supabase",
                return_value=[
                    {
                        "id": 42,
                        "service_type": "tire",
                        "latitude": -23.56,
                        "longitude": -46.64,
                        "user_name": "Ana",
                    }
                ],
            ) as fetch_requests,
        ):
            events = asyncio.run(consume())

        fetch_requests.assert_called_once_with("session-token")
        self.assertEqual(events, [None])
        self.assertFalse(state.pending_requests_loading)
        self.assertEqual(state.pending_requests_error, "")
        self.assertEqual(state.available_requests[0]["id"], 42)
        self.assertEqual(state.available_requests[0]["user"], "Ana")

    def test_provider_home_load_failure_keeps_safe_retry_state(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "pending_requests_loading": False,
            "pending_requests_error": "",
            "available_requests": [],
            "current_provider_id": 1,
            "provider_locations": {},
            "providers": [],
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.load_pending_requests()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch(
                "sosdrive.fetch_pending_requests_supabase",
                side_effect=SupabaseBackendError(503, "private backend detail"),
            ) as fetch_requests,
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            asyncio.run(consume())

        fetch_requests.assert_called_once_with("session-token")
        self.assertFalse(state.pending_requests_loading)
        self.assertEqual(
            state.pending_requests_error,
            "Não foi possível carregar os chamados próximos. Tente novamente.",
        )
        self.assertNotIn("private backend detail", "\n".join(captured.output))

    def test_provider_home_reset_preserves_availability(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "is_available", False)
        object.__setattr__(state, "selected_request", {"id": 10})

        state.reset_provider_home()

        self.assertFalse(state.is_available)
        self.assertEqual(state.selected_request, {})

    def test_leaflet_map_initializer_replaces_detached_route_container(self):
        source = Path(inspect.getfile(OperationalState)).read_text(encoding="utf-8")

        self.assertIn("existingMap.getContainer() === container && container.isConnected", source)
        self.assertIn("existingMap.remove();", source)
        self.assertIn("map.invalidateSize({ pan: false })", source)

    def test_supabase_pending_request_maps_to_provider_queue(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "current_provider_id", "provider-1")
        object.__setattr__(
            state,
            "provider_locations",
            {"provider-1": {"lat": -23.55, "lng": -46.63}},
        )
        object.__setattr__(state, "providers", [])

        mapped = state._map_service_request_to_ui(
            {
                "id": 42,
                "service_type": "tire",
                "latitude": -23.56,
                "longitude": -46.64,
                "user_name": "Ana",
                "vehicle_brand": "Fiat",
                "vehicle_model": "Uno",
                "vehicle_plate": "ABC1234",
            }
        )

        self.assertEqual(mapped["id"], 42)
        self.assertEqual(mapped["type"], "Troca de Pneu")
        self.assertEqual(mapped["user"], "Ana")
        self.assertEqual(mapped["vehicle"], "Fiat Uno ABC1234")
        self.assertEqual(mapped["coords"], [-23.56, -46.64])
        self.assertIn("destination=-23.56,-46.64", mapped["maps_url"])

    def test_provider_home_header_and_map_recenter_action_overlay_the_map(self):
        screen = provider_home_screen()
        header = screen.children[0]

        def find_fixed_buttons(component):
            matches = []
            if (
                getattr(component, "tag", None) == "Button"
                and getattr(component, "position", None) == "fixed"
            ):
                matches.append(component)
            for child in getattr(component, "children", ()):
                if hasattr(child, "children"):
                    matches.extend(find_fixed_buttons(child))
            return matches

        recenter_buttons = find_fixed_buttons(screen)

        self.assertEqual(header.position, "fixed")
        self.assertGreater(int(header.z_index), 1000)
        self.assertEqual(len(recenter_buttons), 1)
        self.assertGreater(int(recenter_buttons[0].z_index), 1000)

    def test_provider_availability_toggle_updates_state_and_matching_provider(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "is_available", True)
        object.__setattr__(state, "current_provider_id", 1)
        object.__setattr__(
            state,
            "providers",
            [{"id": 1, "status": "online"}, {"id": 2, "status": "offline"}],
        )

        state.toggle_provider_status()

        self.assertFalse(state.is_available)
        self.assertEqual(state.providers[0]["status"], "offline")
        self.assertEqual(state.providers[1]["status"], "offline")

        state.toggle_provider_status()

        self.assertTrue(state.is_available)
        self.assertEqual(state.providers[0]["status"], "online")

    def test_project_environment_loads_dotenv_without_overriding_process_values(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / ".env"
            env_file.write_text(
                "SOSDRIVE_TEST_ENV=loaded-from-file\n"
                "SOSDRIVE_TEST_EXISTING=from-file\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"SOSDRIVE_TEST_EXISTING": "from-process"},
                clear=False,
            ):
                os.environ.pop("SOSDRIVE_TEST_ENV", None)
                self.assertTrue(_load_project_environment(env_file))
                self.assertEqual(os.environ["SOSDRIVE_TEST_ENV"], "loaded-from-file")
                self.assertEqual(os.environ["SOSDRIVE_TEST_EXISTING"], "from-process")
                os.environ.pop("SOSDRIVE_TEST_ENV", None)

    def test_message_send_does_not_log_raw_network_exception(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "message_draft": "private conversation",
            "atendimento_mock": {"id": 42},
            "message_error": "",
            "service_messages": [],
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="secret-auth-token"),
            ),
            patch(
                "sosdrive.send_service_message_supabase",
                side_effect=requests.ConnectionError("private network detail"),
            ),
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            asyncio.run(state.send_message())

        log_output = "\n".join(captured.output)
        self.assertIn("ConnectionError", log_output)
        self.assertNotIn("private conversation", log_output)
        self.assertNotIn("secret-auth-token", log_output)
        self.assertNotIn("private network detail", log_output)
        self.assertEqual(state.message_error, "Não foi possível enviar a mensagem.")

    def test_message_authorization_failure_reports_safe_error(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "message_draft": "private conversation",
            "atendimento_mock": {"id": 42},
            "message_error": "",
            "service_messages": [],
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="secret-auth-token"),
            ),
            patch(
                "sosdrive.send_service_message_supabase",
                side_effect=SupabaseBackendError(403, "private database details"),
            ),
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            asyncio.run(state.send_message())

        log_output = "\n".join(captured.output)
        self.assertIn("status=403", log_output)
        self.assertNotIn("private database details", log_output)
        self.assertNotIn("private conversation", log_output)
        self.assertNotIn("secret-auth-token", log_output)
        self.assertEqual(state.message_error, "Não foi possível enviar a mensagem.")


if __name__ == "__main__":
    unittest.main()
