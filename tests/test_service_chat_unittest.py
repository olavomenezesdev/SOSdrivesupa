import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from supabase_backend import SupabaseBackendError
from sosdrive import (
    OperationalState,
    client_message_panel,
    customer_dashboard,
    provider_service_progress_screen,
    service_message_panel,
)


def walk_components(component):
    yield component
    for child in getattr(component, "children", ()):
        if hasattr(child, "children"):
            yield from walk_components(child)


class TestServiceChat(unittest.TestCase):
    def make_state(self, *, provider_panel=False, client_panel=False, request_id=42):
        state = OperationalState.__new__(OperationalState)
        values = {
            "dirty_vars": set(),
            "atendimento_mock": {"id": request_id} if provider_panel else {},
            "request_id": request_id if client_panel else None,
            "show_message_panel": provider_panel,
            "show_client_message_panel": client_panel,
            "active_message_request_id": request_id,
            "message_poll_generation": 1,
            "message_sync_status": "",
            "service_messages": [{"id": 1, "message_text": "old"}],
        }
        for key, value in values.items():
            object.__setattr__(state, key, value)
        return state

    def test_provider_conversation_refresh_replaces_messages_without_duplicates(self):
        state = self.make_state(provider_panel=True)
        refreshed = [
            {"id": 1, "message_text": "old"},
            {"id": 2, "message_text": "new from client"},
        ]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="provider-token"),
            ),
            patch("sosdrive.fetch_service_messages_supabase", return_value=refreshed) as fetch,
        ):
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertTrue(result)
        self.assertEqual(state.service_messages, refreshed)
        self.assertEqual([message["id"] for message in state.service_messages], [1, 2])
        self.assertEqual(state.message_sync_status, "Atualização automática ativa.")
        fetch.assert_called_once_with("provider-token", 42)

    def test_client_conversation_refreshes_its_active_request(self):
        state = self.make_state(provider_panel=False, client_panel=True)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="client-token"),
            ),
            patch(
                "sosdrive.fetch_service_messages_supabase",
                return_value=[{"id": 2, "message_text": "reply from provider"}],
            ) as fetch,
        ):
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertTrue(result)
        self.assertEqual(state.service_messages[0]["message_text"], "reply from provider")
        fetch.assert_called_once_with("client-token", 42)

    def test_refresh_failure_preserves_messages_and_reports_retry(self):
        state = self.make_state(provider_panel=True)
        existing_messages = list(state.service_messages)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="provider-token"),
            ),
            patch(
                "sosdrive.fetch_service_messages_supabase",
                side_effect=SupabaseBackendError(503),
            ),
            self.assertLogs("sosdrive", level="ERROR"),
        ):
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertFalse(result)
        self.assertEqual(state.service_messages, existing_messages)
        self.assertIn("Tentando novamente", state.message_sync_status)

    def test_closed_or_changed_conversation_is_not_refreshed(self):
        state = self.make_state(provider_panel=True)
        state.show_message_panel = False

        with patch("sosdrive.fetch_service_messages_supabase") as fetch:
            result = asyncio.run(state.refresh_open_service_messages(42))

        self.assertFalse(result)
        fetch.assert_not_called()

    def test_closing_provider_conversation_invalidates_its_poll_loop(self):
        state = self.make_state(provider_panel=True)
        generation = state.message_poll_generation

        state.close_message_panel()

        self.assertFalse(state.show_message_panel)
        self.assertIsNone(state.active_message_request_id)
        self.assertEqual(state.message_poll_generation, generation + 1)

    def test_background_poll_runs_every_two_seconds_and_stops_on_close(self):
        state = self.make_state(provider_panel=True)
        delays = []

        async def sleep_and_close_after_one_refresh(delay):
            delays.append(delay)
            if len(delays) == 2:
                state.close_message_panel()

        async def run_poll():
            with (
                patch("sosdrive.asyncio.sleep", new=sleep_and_close_after_one_refresh),
                patch.object(
                    OperationalState,
                    "_get_auth_token",
                    new=AsyncMock(return_value="provider-token"),
                ),
                patch("sosdrive.fetch_service_messages_supabase", return_value=[]) as fetch,
            ):
                await OperationalState.poll_service_messages.fn(state)
            return fetch

        fetch = asyncio.run(run_poll())

        self.assertEqual(delays, [2, 2])
        self.assertEqual(fetch.call_count, 1)
        self.assertFalse(state.show_message_panel)

    def test_provider_and_client_chat_buttons_start_their_polling_loop(self):
        cases = (
            (provider_service_progress_screen(), "open_message_panel"),
            (customer_dashboard(), "open_client_message_panel"),
        )

        for screen, open_handler in cases:
            with self.subTest(open_handler=open_handler):
                event_chains = []
                for component in walk_components(screen):
                    trigger = component.event_triggers.get("on_click")
                    event_names = [
                        event.handler.fn.__name__
                        for event in getattr(trigger, "events", ())
                    ]
                    if open_handler in event_names:
                        event_chains.append(event_names)
                self.assertEqual(len(event_chains), 1)
                self.assertEqual(
                    event_chains[0],
                    [open_handler, "poll_service_messages"],
                )

    def test_both_chat_panels_build_with_accessible_sync_status(self):
        for panel in (service_message_panel(), client_message_panel()):
            components = list(walk_components(panel))
            status_regions = [
                component
                for component in components
                if getattr(component, "tag", None) == "Text"
                and getattr(getattr(component, "role", None), "_var_value", None) == "status"
            ]
            self.assertEqual(len(status_regions), 1)
            self.assertEqual(status_regions[0].custom_attrs.get("aria-live"), "polite")
            self.assertTrue(any(getattr(component, "tag", None) == "Button" for component in components))


if __name__ == "__main__":
    unittest.main()
