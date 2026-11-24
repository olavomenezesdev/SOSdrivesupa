import asyncio
import inspect
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, call, patch

import httpx
import requests

from supabase_backend import (
    SupabaseBackendError,
    create_service_request as create_service_request_backend,
    fetch_active_service_requests,
    fetch_pending_requests,
)
from styles import GLOBAL_STYLE
from sosdrive import (
    AuthState,
    OperationalState,
    _load_project_environment,
    payment_api,
    customer_dashboard,
    profile_screen,
    payment_screen,
    provider_home_screen,
    provider_service_progress_screen,
    review_screen,
    service_details_screen,
    user_home_screen,
    waiting_payment_screen,
)


class TestSupabaseRuntime(unittest.TestCase):
    def render_component(self, component):
        return re.sub(
            r"\\u([0-9a-fA-F]{4})",
            lambda match: chr(int(match.group(1), 16)),
            str(component),
        )

    def test_asaas_checkout_return_redirects_to_frontend_payment(self):
        async def send_callback():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=payment_api),
                base_url="http://testserver",
            ) as client:
                return await client.get(
                    "/api/asaas/checkout-return/success",
                    follow_redirects=False,
                )

        with patch.dict(
            os.environ,
            {"ASAAS_CHECKOUT_FRONTEND_URL": "http://localhost:3000"},
        ):
            response = asyncio.run(send_callback())

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://localhost:3000/payment")

    def test_provider_home_renders_empty_loading_error_and_retry_feedback(self):
        screen = provider_home_screen()
        rendered = self.render_component(screen)

        self.assertIn("Nenhum chamado ou cliente próximo no momento", rendered)
        self.assertIn("Carregando chamados próximos...", rendered)
        self.assertIn("pending_requests_error_rx_state_", rendered)
        self.assertIn("Tentar novamente", rendered)
        self.assertIn("load_pending_requests", rendered)
        self.assertIn("Solicitações Próximas", rendered)
        self.assertIn("Pagar atendimento", self.render_component(customer_dashboard()))
        mount_events = screen.event_triggers["on_mount"].events
        self.assertEqual(
            [event.handler.fn.__name__ for event in mount_events],
            [
                "ensure_provider_payment_complete",
                "reset_provider_home",
                "load_pending_requests",
                "poll_pending_requests",
            ],
        )

    def test_client_home_explains_no_active_call_and_keeps_request_action(self):
        rendered = self.render_component(user_home_screen())

        self.assertIn("Você ainda não tem um chamado em andamento. Solicite socorro quando precisar.", rendered)
        self.assertIn("Solicitar Socorro", rendered)
        self.assertIn("Chamado em andamento", rendered)

    def test_payment_and_review_screens_use_hosted_checkout_and_payment_guards(self):
        payment_component = payment_screen()
        payment = self.render_component(payment_component)
        waiting = waiting_payment_screen()
        review = review_screen()

        self.assertIn("Checkout seguro Asaas", payment)
        self.assertIn("Cartão de Crédito", payment)
        self.assertIn("Continuar no checkout seguro", payment)
        self.assertIn("Status: aguardando confirmação", payment)
        self.assertIn("Atualizar status do pagamento", payment)
        self.assertNotIn(">Pix<", payment)
        self.assertNotIn("Pagar na máquina", payment)
        self.assertNotIn("Confirmar pagamento na máquina", payment)
        self.assertEqual(payment.count("payment-method-card"), 1)
        self.assertNotIn("Número do cartão", payment)
        self.assertNotIn("CVV", payment)
        self.assertEqual(
            [
                event.handler.fn.__name__
                for event in payment_component.event_triggers["on_mount"].events
            ],
            ["load_payment_context", "poll_customer_payment"],
        )
        self.assertIn("Aguardando pagamento", self.render_component(waiting))
        self.assertIn(
            "Voltar para meus chamados",
            self.render_component(review),
        )
        self.assertIn("/home_client", self.render_component(review))
        self.assertEqual(
            waiting.event_triggers["on_mount"].events[0].handler.fn.__name__,
            "poll_provider_payment",
        )
        self.assertEqual(
            review.event_triggers["on_mount"].events[0].handler.fn.__name__,
            "ensure_review_payment_confirmed",
        )
        self.assertIn(
            "Sua avaliação já foi registrada",
            self.render_component(review),
        )

    def test_refresh_payment_status_requests_gateway_reconciliation(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "request_id": 42,
            "payment_error": "",
            "payment_message": "",
            "payment_status": "pending",
            "payment_amount": 0.0,
            "checkout_url": "https://checkout.example",
        }.items():
            object.__setattr__(state, name, value)
        auth_state = type("Auth", (), {"auth_token": "session-token"})()
        object.__setattr__(state, "get_state", AsyncMock(return_value=auth_state))

        with patch(
            "sosdrive.asyncio.to_thread",
            new=AsyncMock(
                return_value={
                    "status": "pending",
                    "payment_method": "credit_card",
                    "amount": 57.84,
                    "checkout_url": "https://checkout.example",
                }
            ),
        ) as fetch_status:
            asyncio.run(OperationalState.refresh_payment_status.fn(state))

        fetch_status.assert_awaited_once()
        self.assertTrue(fetch_status.await_args.kwargs["reconcile_with_gateway"])
        self.assertEqual(state.payment_status, "pending")
        self.assertIn("Asaas", state.payment_message)
        self.assertEqual(state.payment_error, "")

    def test_provider_can_submit_review_using_attendance_request_id(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "review_loading": False,
            "review_rating": 5,
            "review_comment": "Ótimo atendimento",
            "review_error": "",
            "review_message": "",
            "review_already_submitted": False,
            "request_id": None,
            "atendimento_mock": {"id": 42},
        }.items():
            object.__setattr__(state, name, value)
        auth_state = type("Auth", (), {"auth_token": "session-token"})()
        app_state = type("App", (), {"user_role": "prestador"})()
        object.__setattr__(
            state,
            "get_state",
            AsyncMock(side_effect=[auth_state, app_state]),
        )

        async def submit_review(_submit_function, _token, request_id, rating, comment):
            self.assertEqual(request_id, 42)
            self.assertEqual(rating, 5)
            self.assertEqual(comment, "Ótimo atendimento")

        with patch(
            "sosdrive.asyncio.to_thread",
            new=AsyncMock(side_effect=submit_review),
        ) as submit:
            async def consume():
                return [
                    event
                    async for event in OperationalState.submit_review.fn(state)
                ]

            events = asyncio.run(consume())

        submit.assert_awaited_once()
        self.assertEqual(state.request_id, 42)
        self.assertTrue(state.review_already_submitted)
        self.assertEqual(state.review_message, "Avaliação enviada com sucesso.")
        self.assertEqual(state.review_error, "")
        self.assertFalse(state.review_loading)
        self.assertIn("/home_provider", str(events[-1]))

    def test_review_submission_reports_missing_request_id(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "review_loading": False,
            "request_id": None,
            "atendimento_mock": {},
            "review_error": "",
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [
                event
                async for event in OperationalState.submit_review.fn(state)
            ]

        asyncio.run(consume())

        self.assertIn("identificar o chamado", state.review_error)

    def test_customer_returns_home_after_submitting_review(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "review_loading": False,
            "review_rating": 4,
            "review_comment": "Bom atendimento",
            "review_error": "",
            "review_message": "",
            "review_already_submitted": False,
            "request_id": 42,
            "atendimento_mock": {},
        }.items():
            object.__setattr__(state, name, value)
        auth_state = type("Auth", (), {"auth_token": "session-token"})()
        app_state = type("App", (), {"user_role": "cliente"})()
        object.__setattr__(
            state,
            "get_state",
            AsyncMock(side_effect=[auth_state, app_state]),
        )

        with patch(
            "sosdrive.asyncio.to_thread",
            new=AsyncMock(return_value={"rating": 4}),
        ):
            async def consume():
                return [
                    event
                    async for event in OperationalState.submit_review.fn(state)
                ]

            events = asyncio.run(consume())

        self.assertIn("/home_client", str(events[-1]))

    def test_existing_customer_review_can_return_to_home(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "request_id": 42,
            "atendimento_mock": {},
            "review_already_submitted": False,
            "review_rating": 0,
            "review_comment": "",
            "review_message": "",
        }.items():
            object.__setattr__(state, name, value)
        app_state = type("App", (), {"user_role": "cliente"})()
        object.__setattr__(state, "get_state", AsyncMock(return_value=app_state))

        with (
            patch("sosdrive.OperationalState._get_auth_token", new=AsyncMock(return_value="session-token")),
            patch(
                "sosdrive.asyncio.to_thread",
                new=AsyncMock(
                    side_effect=[
                        {"status": "confirmed"},
                        {"rating": 5, "comment": "Atendimento ótimo"},
                    ]
                ),
            ) as backend_call,
        ):
            asyncio.run(OperationalState.ensure_review_payment_confirmed.fn(state))

        self.assertEqual(backend_call.await_count, 2)
        self.assertTrue(state.review_already_submitted)
        self.assertEqual(state.review_rating, 5)
        self.assertEqual(state.review_comment, "Atendimento ótimo")
        self.assertEqual(state.review_message, "Você já avaliou este atendimento. Obrigado!")

    def test_provider_earnings_load_for_authenticated_provider(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "provider_earnings_balance", 0.0)
        object.__setattr__(state, "provider_earnings_error", "")
        app_state = type("App", (), {"user_role": "prestador"})()
        auth_state = type("Auth", (), {"auth_token": "session-token"})()
        object.__setattr__(state, "get_state", AsyncMock(side_effect=[app_state, auth_state]))

        with patch(
            "sosdrive.asyncio.to_thread",
            new=AsyncMock(return_value={"balance": 116.46, "count": 2}),
        ) as fetch_balance:
            asyncio.run(OperationalState.load_provider_earnings.fn(state))

        fetch_balance.assert_awaited_once()
        self.assertEqual(state.provider_earnings_balance, 116.46)
        self.assertEqual(state.provider_earnings_error, "")

    def test_provider_earnings_are_not_loaded_for_customer(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "provider_earnings_balance", 50.0)
        object.__setattr__(state, "provider_earnings_error", "")
        app_state = type("App", (), {"user_role": "cliente"})()
        object.__setattr__(state, "get_state", AsyncMock(return_value=app_state))

        with patch("sosdrive.asyncio.to_thread", new=AsyncMock()) as fetch_balance:
            asyncio.run(OperationalState.load_provider_earnings.fn(state))

        fetch_balance.assert_not_awaited()
        self.assertEqual(state.provider_earnings_balance, 0.0)

    def test_payment_context_formats_service_date_and_amount_in_portuguese(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "payment_error": "",
            "request_id": None,
            "payment_status": "not_created",
            "checkout_url": "",
        }.items():
            object.__setattr__(state, name, value)
        auth_state = type("Auth", (), {"auth_token": "session-token"})()
        object.__setattr__(state, "get_state", AsyncMock(return_value=auth_state))

        with patch(
            "sosdrive.asyncio.to_thread",
            new=AsyncMock(
                side_effect=[
                    {
                        "request_id": 42,
                        "service_type": "mechanical",
                        "estimated_price": 117.26,
                        "distance_km": 12.419,
                        "created_at": "2026-11-23T12:15:00Z",
                        "provider_name": "Prestador",
                        "vehicle_description": "Veículo",
                    },
                    {"status": "pending", "amount": 117.26, "checkout_url": ""},
                ]
            ),
        ):
            asyncio.run(OperationalState.load_payment_context.fn(state))

        self.assertEqual(state.payment_service_name, "Mecânica")
        self.assertEqual(state.payment_created_at, "23/11/2026")
        self.assertEqual(state.payment_total_text, "R$ 117,26")
        object.__setattr__(state, "provider_earnings_balance", 1250.5)
        self.assertEqual(state.provider_earnings_balance_text, "R$ 1.250,50")

    def test_payment_poll_workers_read_authentication_inside_state_lock(self):
        async def verify_worker(worker, state_values):
            state = OperationalState.__new__(OperationalState)
            for name, value in {"dirty_vars": set(), **state_values}.items():
                object.__setattr__(state, name, value)
            object.__setattr__(state, "locked", False)
            original_enter = OperationalState.__aenter__
            original_exit = OperationalState.__aexit__

            async def tracked_enter(current_state):
                result = await original_enter(current_state)
                object.__setattr__(current_state, "locked", True)
                return result

            async def tracked_exit(current_state, *args):
                object.__setattr__(current_state, "locked", False)
                return await original_exit(current_state, *args)

            async def get_auth_token(current_state):
                self.assertTrue(current_state.locked)
                raise asyncio.CancelledError()

            with (
                patch.object(OperationalState, "__aenter__", new=tracked_enter),
                patch.object(OperationalState, "__aexit__", new=tracked_exit),
                patch.object(OperationalState, "_get_auth_token", new=get_auth_token),
            ):
                with self.assertRaises(asyncio.CancelledError):
                    await worker.fn(state)
            self.assertFalse(state.locked)

        asyncio.run(
            verify_worker(
                OperationalState.poll_customer_payment,
                {"request_id": 42},
            )
        )
        asyncio.run(
            verify_worker(
                OperationalState.poll_provider_payment,
                {"request_id": 42, "atendimento_mock": {"id": 42}},
            )
        )

    def make_customer_poll_state(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "request_id": 42,
            "request_server_status": "pending",
            "request_status": "searching",
            "request_estimated_price": 50.0,
            "request_distance_km": 2.5,
            "request_poll_error": "",
            "service_messages": [{"message_text": "Olá"}],
            "client_message_draft": "Ainda estou no local",
            "show_client_message_panel": True,
            "active_message_request_id": 42,
        }.items():
            object.__setattr__(state, name, value)
        object.__setattr__(state, "_get_auth_token", AsyncMock(return_value="client-token"))
        return state

    def test_customer_poll_tracks_persisted_statuses_until_terminal(self):
        state = self.make_customer_poll_state()
        cases = (
            ("pending", "searching", True),
            ("accepted", "matched", True),
            ("in_progress", "matched", True),
            ("completed", "completed", False),
            ("cancelled", "cancelled", False),
            ("future_status", "unknown", True),
        )

        for index, (server_status, presentation_status, pollable) in enumerate(cases):
            with self.subTest(status=server_status):
                object.__setattr__(state, "request_server_status", "pending")
                object.__setattr__(state, "request_status", "searching")
                with patch(
                    "sosdrive.fetch_service_request_supabase",
                    return_value={
                        "id": 42,
                        "status": server_status,
                        "estimated_price": 70 + index,
                        "distance_km": 3 + index,
                    },
                ) as fetch_request:
                    asyncio.run(state._poll_customer_request_once())

                fetch_request.assert_called_once_with("client-token", 42)
                self.assertEqual(state.request_server_status, server_status)
                self.assertEqual(state.request_status, presentation_status)
                self.assertEqual(state._customer_request_is_pollable(), pollable)
                self.assertEqual(state.request_estimated_price, 70 + index)
                self.assertEqual(state.request_distance_km, 3 + index)

    def test_customer_poll_error_preserves_request_and_chat_state(self):
        state = self.make_customer_poll_state()

        with patch(
            "sosdrive.fetch_service_request_supabase",
            side_effect=requests.RequestException("temporary network failure"),
        ):
            asyncio.run(state._poll_customer_request_once())

        self.assertEqual(state.request_id, 42)
        self.assertEqual(state.request_server_status, "pending")
        self.assertEqual(state.request_status, "searching")
        self.assertIn("Tentando novamente", state.request_poll_error)
        self.assertEqual(state.service_messages, [{"message_text": "Olá"}])
        self.assertEqual(state.client_message_draft, "Ainda estou no local")
        self.assertTrue(state.show_client_message_panel)
        self.assertEqual(state.active_message_request_id, 42)

    def test_customer_poll_displays_in_progress_without_clearing_open_chat(self):
        state = self.make_customer_poll_state()
        with patch(
            "sosdrive.fetch_service_request_supabase",
            return_value={
                "id": 42,
                "status": "in_progress",
                "estimated_price": 50.0,
                "distance_km": 2.5,
            },
        ):
            asyncio.run(state._poll_customer_request_once())

        self.assertEqual(state.request_server_status, "in_progress")
        self.assertEqual(state.request_status, "matched")
        self.assertEqual(state.service_messages, [{"message_text": "Olá"}])
        self.assertEqual(state.client_message_draft, "Ainda estou no local")
        self.assertTrue(state.show_client_message_panel)
        self.assertEqual(state.active_message_request_id, 42)

    def test_customer_completed_request_redirects_to_payment(self):
        state = self.make_customer_poll_state()
        object.__setattr__(state, "payment_redirect_pending", False)
        with patch(
            "sosdrive.fetch_service_request_supabase",
            return_value={
                "id": 42,
                "status": "completed",
                "estimated_price": 50.0,
                "distance_km": 2.5,
            },
        ):
            event = asyncio.run(
                OperationalState.poll_service_request_status.fn(state)
            )

        self.assertIn("/payment", str(event))
        self.assertEqual(state.request_server_status, "completed")
        self.assertEqual(state.request_status, "completed")
        self.assertFalse(state.payment_redirect_pending)

    def test_customer_request_statuses_have_safe_labels_and_actions(self):
        state = self.make_customer_poll_state()
        cases = (
            ("pending", "searching"),
            ("accepted", "matched"),
            ("in_progress", "matched"),
            ("completed", "completed"),
            ("cancelled", "cancelled"),
            ("future_status", "unknown"),
        )

        for server_status, presentation in cases:
            with self.subTest(status=server_status):
                state._apply_customer_request_snapshot(
                    {"status": server_status, "estimated_price": 75, "distance_km": 4.2}
                )
                self.assertEqual(state.request_status, presentation)
                self.assertEqual(state.request_server_status, server_status)

    def test_customer_cannot_cancel_accepted_request_and_can_cancel_pending(self):
        state = self.make_customer_poll_state()
        object.__setattr__(state, "_get_auth_token", AsyncMock(return_value="client-token"))
        with patch("sosdrive.cancel_service_request_supabase") as cancel_request:
            state._apply_customer_request_snapshot({"status": "accepted"})
            asyncio.run(state.set_request_status("idle"))
            cancel_request.assert_not_called()

            state._apply_customer_request_snapshot({"status": "pending"})
            cancel_request.return_value = {"id": 42, "status": "cancelled"}
            asyncio.run(state.set_request_status("idle"))

        cancel_request.assert_called_once_with("client-token", 42)
        self.assertIsNone(state.request_id)
        self.assertEqual(state.request_status, "cancelled")
        self.assertEqual(state.request_server_status, "cancelled")

    def test_customer_dashboard_layout_preserves_existing_actions_and_map(self):
        screen = customer_dashboard()
        rendered = self.render_component(screen)
        source = inspect.getsource(customer_dashboard)

        for token in (
            "customer-dashboard-page",
            "customer-dashboard-header",
            "customer-map-frame",
            "customer-request-card",
            "customer-service-grid",
            "customer-service-icon",
            "customer-service-label",
            "customer-availability-pill",
            "customer-availability-dot",
            "Centralizar no meu local",
            "Do que você precisa?",
            "Buscando o melhor profissional...",
            "Profissional a caminho!",
            "Atendimento em andamento",
            "Atendimento concluído!",
            "O chamado foi cancelado.",
            "Atualizando status do chamado",
            "Preço estimado:",
            "Distância:",
            "Cancelar Pedido",
            "Fechar resumo",
            "Mensagens do chamado",
            "request_server_status_rx_state_",
            "request_status_rx_state_",
            "request_id_rx_state_",
            "Ir para o perfil",
            "Pneu Furado",
            "Bateria",
            "Mecânica",
            "Combustível",
            "online_providers_count_rx_state_",
            "request_error_message_rx_state_",
            "request_price_text_rx_state_",
            "request_distance_text_rx_state_",
            "show_vehicle_selection_rx_state_",
            "submit_customer_request",
            "open_client_message_panel",
            "poll_service_messages",
            "set_request_status",
            "open_profile_for_request",
            "customer-map",
        ):
            with self.subTest(token=token):
                self.assertIn(token, rendered)

        self.assertIn(
            "window.initSOSMap('customer-map', [-23.5505, -46.6333], 13);",
            source,
        )
        self.assertIn("window.centerMap('customer-map')", source)
        self.assertIn("window.updateUserMarker('customer-map', lat, lng)", source)
        self.assertIn('id="lat-lng-trigger"', source)
        self.assertNotIn("window.showSOSRoute('customer-map'", source)

    def test_customer_dashboard_styles_are_scoped_and_responsive(self):
        mobile_styles = GLOBAL_STYLE["@media (max-width: 720px)"]
        small_styles = GLOBAL_STYLE["@media (max-width: 420px)"]
        tablet_styles = GLOBAL_STYLE["@media (max-width: 1024px)"]

        self.assertIn(".customer-dashboard-page", GLOBAL_STYLE)
        self.assertIn(
            "linear-gradient",
            GLOBAL_STYLE[".customer-dashboard-page"]["background"],
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-dashboard-content"]["grid_template_columns"],
            "minmax(0, 1.8fr) minmax(340px, 1fr)",
        )
        self.assertEqual(
            tablet_styles[".customer-dashboard-content"]["grid_template_columns"],
            "minmax(0, 1fr)",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-dashboard-layout"]["max_width"],
            "1680px",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-dashboard-page"]["height"],
            "100vh",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-map-frame"]["height"],
            "100%",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-availability-pill"]["white_space"],
            "nowrap",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-availability-dot"]["width"],
            "8px",
        )
        self.assertNotIn(
            "box_shadow",
            GLOBAL_STYLE[".customer-availability-dot"],
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-service-icon"]["width"],
            "48px",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-service-card"]["min_height"],
            "120px",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-service-label"]["font_size"],
            "15px",
        )
        self.assertIn(".customer-dashboard-content", mobile_styles)
        self.assertIn(".customer-availability-pill", small_styles)
        self.assertEqual(
            GLOBAL_STYLE[".customer-request-success"]["background"],
            "#F0FDF4",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-messages-button"]["background"],
            "#1E3A8A",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-status-banner.is-in-progress"]["background"],
            "#FFF7ED",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-status-banner.is-completed"]["color"],
            "#166534",
        )
        self.assertEqual(
            GLOBAL_STYLE[".customer-request-progress"]["grid_template_columns"],
            "repeat(4, minmax(0, 1fr))",
        )
        self.assertIn(".customer-summary-clear-button", GLOBAL_STYLE)
        self.assertNotIn(".customer-dashboard-page", GLOBAL_STYLE[".user-home-root"])

    def test_profile_return_routes_to_role_specific_home(self):
        rendered = self.render_component(profile_screen())

        self.assertIn("/home_provider", rendered)
        self.assertIn("/home_client", rendered)
        self.assertIn("Voltar", rendered)
        self.assertIn("Sair", rendered)
        self.assertIn("Ganhos confirmados", rendered)
        self.assertIn("Saldo interno dos atendimentos pagos", rendered)
        self.assertIn(
            "load_provider_earnings",
            [
                event.handler.fn.__name__
                for event in profile_screen().event_triggers["on_mount"].events
            ],
        )

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
        profile_source = inspect.getsource(profile_screen)
        vehicle_source_start = profile_source.index('class_name="profile-vehicles-section"')
        vehicle_condition_start = profile_source.rfind(
            'AppState.user_role != "prestador"',
            0,
            vehicle_source_start,
        )
        self.assertGreater(vehicle_condition_start, -1)
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
            "atendimento_mock": {},
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.load_pending_requests()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_identity",
                new=AsyncMock(return_value=("session-token", "provider-1")),
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
            patch(
                "sosdrive.fetch_active_service_requests_supabase",
                return_value=[],
            ) as fetch_active,
            self.assertLogs("sosdrive", level="INFO") as captured,
        ):
            events = asyncio.run(consume())

        fetch_requests.assert_called_once_with("session-token")
        fetch_active.assert_called_once_with("session-token", "provider-1")
        self.assertEqual(events, [None])
        self.assertFalse(state.pending_requests_loading)
        self.assertEqual(state.pending_requests_error, "")
        self.assertEqual(state.available_requests[0]["id"], 42)
        self.assertEqual(state.available_requests[0]["user"], "Ana")
        log_output = "\n".join(captured.output)
        self.assertIn("Provider request initial load started", log_output)
        self.assertIn("Provider request initial load applied count=1", log_output)
        self.assertNotIn("session-token", log_output)
        self.assertNotIn("provider-1", log_output)
        self.assertNotIn("Ana", log_output)

    def test_provider_poll_guard_skips_duplicate_background_worker(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "pending_requests_polling", True)

        with patch("sosdrive.asyncio.sleep", new_callable=AsyncMock) as sleep:
            asyncio.run(OperationalState.poll_pending_requests.fn(state))

        sleep.assert_not_awaited()

    def test_provider_poll_reads_identity_inside_state_lock(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "locked", False)
        object.__setattr__(state, "pending_requests_polling", False)

        original_enter = OperationalState.__aenter__
        original_exit = OperationalState.__aexit__

        async def tracked_enter(current_state):
            result = await original_enter(current_state)
            object.__setattr__(current_state, "locked", True)
            return result

        async def tracked_exit(current_state, *args):
            object.__setattr__(current_state, "locked", False)
            return await original_exit(current_state, *args)

        async def get_identity(current_state):
            self.assertTrue(current_state.locked)
            raise asyncio.CancelledError()

        with (
            patch("sosdrive.asyncio.sleep", new_callable=AsyncMock) as sleep,
            patch.object(OperationalState, "__aenter__", new=tracked_enter),
            patch.object(OperationalState, "__aexit__", new=tracked_exit),
            patch.object(OperationalState, "_get_auth_identity", new=get_identity),
        ):
            sleep.return_value = None
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(OperationalState.poll_pending_requests.fn(state))

        self.assertFalse(state.pending_requests_polling)

    def test_provider_poll_waits_for_initial_load_and_releases_guard_on_cancel(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "pending_requests_polling": False,
            "pending_requests_loading": False,
            "pending_requests_error": "",
            "available_requests": [],
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch("sosdrive.asyncio.sleep", new_callable=AsyncMock) as sleep,
            patch.object(
                OperationalState,
                "_get_auth_identity",
                new=AsyncMock(return_value=("session-token", "provider-1")),
            ),
            patch.object(
                OperationalState,
                "_fetch_provider_requests",
                new=AsyncMock(return_value=[{"id": 42}]),
            ) as fetch_requests,
        ):
            sleep.side_effect = [None, asyncio.CancelledError()]
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(OperationalState.poll_pending_requests.fn(state))

        sleep.assert_has_awaits([call(20), call(20)])
        fetch_requests.assert_awaited_once_with("session-token", "provider-1")
        self.assertFalse(state.pending_requests_polling)
        self.assertEqual(state.available_requests, [{"id": 42}])

    def test_provider_home_load_failure_keeps_safe_retry_state(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "pending_requests_loading": False,
            "pending_requests_error": "",
            "available_requests": [{"id": 10, "status": "in_progress", "is_active": True}],
            "is_available": True,
            "current_provider_id": 1,
            "provider_locations": {},
            "providers": [],
            "atendimento_mock": {},
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.load_pending_requests()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_identity",
                new=AsyncMock(return_value=("session-token", "provider-1")),
            ),
            patch(
                "sosdrive.fetch_pending_requests_supabase",
                side_effect=SupabaseBackendError(503, "private backend detail"),
            ) as fetch_requests,
            patch(
                "sosdrive.fetch_active_service_requests_supabase",
                return_value=[],
            ),
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            asyncio.run(consume())

        fetch_requests.assert_called_once_with("session-token")
        self.assertFalse(state.pending_requests_loading)
        self.assertEqual(
            state.pending_requests_error,
            "Não foi possível carregar os chamados próximos. Tente novamente.",
        )
        self.assertEqual(state.available_requests[0]["id"], 10)
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
        self.assertFalse(mapped["is_active"])

    def test_pending_request_without_coordinates_stays_visible_and_zero_is_valid(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "current_provider_id", "provider-1")
        object.__setattr__(
            state,
            "provider_locations",
            {"provider-1": {"lat": -23.55, "lng": -46.63}},
        )
        object.__setattr__(state, "providers", [])
        object.__setattr__(state, "available_requests", [])
        object.__setattr__(state, "atendimento_mock", {})

        requests = state._combine_provider_requests(
            [
                {
                    "id": 42,
                    "service_type": "tire",
                    "latitude": None,
                    "longitude": None,
                },
                {
                    "id": 43,
                    "service_type": "battery",
                    "latitude": 0,
                    "longitude": 0,
                },
            ],
            [],
        )

        self.assertEqual([request["id"] for request in requests], [43, 42])
        request_without_location = requests[1]
        self.assertIsNone(request_without_location["coords"])
        self.assertEqual(
            request_without_location["distance"],
            "Distância indisponível",
        )
        self.assertEqual(request_without_location["maps_url"], "")
        self.assertEqual(requests[0]["coords"], [0.0, 0.0])

    def test_attendance_route_is_not_created_without_request_coordinates(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(
            state,
            "atendimento_mock",
            {
                "provider_coords": [-23.55, -46.63],
                "user_coords": None,
            },
        )

        route_script = state.atendimento_route_script

        self.assertIn("window.initSOSMap", route_script)
        self.assertNotIn("window.showSOSRoute", route_script)

    def test_active_request_query_is_scoped_to_provider_and_live_statuses(self):
        class FakeQuery:
            def __init__(self):
                self.filters = []

            def select(self, fields):
                self.selected_fields = fields
                return self

            def eq(self, field, value):
                self.filters.append(("eq", field, value))
                return self

            def in_(self, field, values):
                self.filters.append(("in", field, list(values)))
                return self

            def execute(self):
                return type("Response", (), {"data": [{"id": 42, "status": "accepted"}]})()

        query = FakeQuery()
        client = type(
            "FakeClient",
            (),
            {"table": lambda _self, name: self.assertEqual(name, "service_requests") or query},
        )()

        with patch("supabase_backend._authenticated_client", return_value=client):
            requests = fetch_active_service_requests("session-token", "provider-1")

        self.assertEqual(requests, [{"id": 42, "status": "accepted"}])
        self.assertEqual(
            query.filters,
            [
                ("eq", "provider_id", "provider-1"),
                ("in", "status", ["accepted", "in_progress"]),
            ],
        )

    def test_pending_request_query_reports_invalid_rpc_payload_instead_of_empty_list(self):
        class FakeQuery:
            def execute(self):
                return type("Response", (), {"data": {"unexpected": True}})()

        client = type(
            "FakeClient",
            (),
            {"rpc": lambda _self, name, args: FakeQuery()},
        )()

        with patch("supabase_backend._authenticated_client", return_value=client):
            with self.assertRaises(SupabaseBackendError) as raised:
                fetch_pending_requests("session-token")

        self.assertEqual(raised.exception.status_code, 502)

    def test_pending_request_query_uses_authorized_provider_rpc(self):
        class FakeQuery:
            def execute(self):
                return type("Response", (), {"data": [{"id": 42, "status": "pending"}]})()

        class FakeClient:
            def rpc(self, name, arguments):
                self.rpc_call = (name, arguments)
                return FakeQuery()

        client = FakeClient()
        with patch("supabase_backend._authenticated_client", return_value=client):
            requests = fetch_pending_requests("session-token")

        self.assertEqual(requests, [{"id": 42, "status": "pending"}])
        self.assertEqual(
            client.rpc_call,
            ("list_pending_service_requests", {}),
        )

    def test_create_request_sends_supported_service_and_returns_pending_unassigned_row(self):
        class FakeQuery:
            def execute(self):
                return type(
                    "Response",
                    (),
                    {
                        "data": {
                            "id": 42,
                            "service_type": "tire",
                            "status": "pending",
                            "provider_id": None,
                            "latitude": 0.0,
                            "longitude": 0.0,
                        }
                    },
                )()

        class FakeClient:
            def rpc(self, name, args):
                self.rpc_name = name
                self.rpc_args = args
                return FakeQuery()

        client = FakeClient()
        with patch("supabase_backend._authenticated_client", return_value=client):
            request = create_service_request_backend(
                "session-token",
                "tire",
                7,
                0.0,
                0.0,
            )

        self.assertEqual(client.rpc_name, "create_service_request")
        self.assertEqual(
            client.rpc_args,
            {
                "p_service_type": "tire",
                "p_vehicle_id": 7,
                "p_latitude": 0.0,
                "p_longitude": 0.0,
            },
        )
        self.assertEqual(request["status"], "pending")
        self.assertIsNone(request["provider_id"])
        self.assertEqual(request["request_id"], 42)

    def test_provider_requests_put_active_first_and_sort_pending_by_distance(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "current_provider_id": "provider-1",
            "provider_locations": {
                "provider-1": {"lat": -23.55, "lng": -46.63}
            },
            "providers": [],
            "available_requests": [
                {
                    "id": 42,
                    "type": "Bateria",
                    "service_icon": "🔋",
                    "user": "Ana",
                    "phone": "(11) 99999-0000",
                    "vehicle": "Fiat Uno ABC1234",
                    "note": "Sem observações.",
                    "description": "Pane elétrica",
                    "address": "Rua A",
                    "eta": "10 min",
                    "maps_url": "https://maps.example/42",
                }
            ],
            "atendimento_mock": {},
        }.items():
            object.__setattr__(state, name, value)

        requests = state._combine_provider_requests(
            [
                {
                    "id": 43,
                    "status": "pending",
                    "service_type": "tire",
                    "latitude": -23.56,
                    "longitude": -46.63,
                    "user_name": "Bia",
                },
                {
                    "id": 44,
                    "status": "pending",
                    "service_type": "fuel",
                    "latitude": -23.552,
                    "longitude": -46.63,
                    "user_name": "Caio",
                },
            ],
            [
                {
                    "id": 42,
                    "status": "accepted",
                    "service_type": "battery",
                    "latitude": -23.57,
                    "longitude": -46.63,
                }
            ],
        )

        self.assertEqual([request["id"] for request in requests], [42, 44, 43])
        self.assertTrue(requests[0]["is_active"])
        self.assertEqual(requests[0]["user"], "Ana")
        self.assertEqual(requests[0]["vehicle"], "Fiat Uno ABC1234")
        self.assertFalse(requests[1]["is_active"])

    def test_provider_home_keeps_active_requests_visible_when_unavailable(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "is_available", False)
        object.__setattr__(
            state,
            "available_requests",
            [
                {"id": 42, "is_active": True},
                {"id": 43, "is_active": False},
            ],
        )

        self.assertTrue(state.has_active_requests)
        self.assertEqual(state.provider_home_requests, [{"id": 42, "is_active": True}])
        self.assertEqual(
            state.nearby_requests_summary,
            "1 chamado na sua região, do mais perto ao mais longe.",
        )

    def test_active_request_details_reopen_attendance_without_accepting(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "available_requests": [{"id": 42, "is_active": True, "status": "accepted"}],
            "selected_request": {},
            "atendimento_mock": {"id": 42},
            "atendimento_phase": "NO_LOCAL",
            "providers": [],
            "current_provider_id": 1,
        }.items():
            object.__setattr__(state, name, value)

        event = state.view_request_details(42)

        self.assertIn("/provider-service-progress", str(event))
        self.assertEqual(state.selected_request["id"], 42)
        self.assertEqual(state.atendimento_phase, "NO_LOCAL")

    def test_accept_request_keeps_it_marked_active_in_provider_queue(self):
        state = OperationalState.__new__(OperationalState)
        request = {
            "id": 42,
            "type": "Bateria",
            "status": "pending",
            "is_active": False,
            "user": "Ana",
            "vehicle": "Fiat Uno",
        }
        for name, value in {
            "dirty_vars": set(),
            "available_requests": [request],
            "selected_request": {},
            "atendimento_mock": {},
            "atendimento_phase": "",
            "show_cancel_confirm": False,
            "current_provider_id": 1,
            "providers": [{"id": 1, "coords": [-23.55, -46.63]}],
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch("sosdrive.accept_service_request_supabase"),
        ):
            event = asyncio.run(state.accept_request(42))

        self.assertIn("/provider-service-progress", str(event))
        self.assertEqual(len(state.available_requests), 1)
        self.assertTrue(state.available_requests[0]["is_active"])
        self.assertEqual(state.available_requests[0]["status"], "accepted")
        self.assertEqual(state.atendimento_mock["id"], 42)

    def test_start_attendance_persists_before_updating_provider_phase(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "atendimento_mock": {"id": 42},
            "atendimento_phase": "NO_LOCAL",
            "selected_request": {"id": 42, "status": "accepted", "is_active": True},
            "available_requests": [
                {"id": 42, "status": "accepted", "is_active": True},
                {"id": 43, "status": "pending", "is_active": False},
            ],
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch(
                "sosdrive.start_service_request_supabase",
                return_value={"id": 42, "status": "in_progress"},
            ) as start_request,
        ):
            event = asyncio.run(state.advance_atendimento_phase())

        start_request.assert_called_once_with("session-token", 42)
        self.assertIsNone(event)
        self.assertEqual(state.atendimento_phase, "ATENDENDO")
        self.assertEqual(state.selected_request["status"], "in_progress")
        self.assertTrue(state.selected_request["is_active"])
        self.assertEqual(state.available_requests[0]["status"], "in_progress")
        self.assertEqual(state.available_requests[1]["status"], "pending")

    def test_start_attendance_failure_keeps_provider_at_no_local(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "atendimento_mock": {"id": 42},
            "atendimento_phase": "NO_LOCAL",
            "selected_request": {"id": 42, "status": "accepted", "is_active": True},
            "available_requests": [{"id": 42, "status": "accepted", "is_active": True}],
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch(
                "sosdrive.start_service_request_supabase",
                side_effect=SupabaseBackendError(503, "private backend detail"),
            ) as start_request,
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            event = asyncio.run(state.advance_atendimento_phase())

        start_request.assert_called_once_with("session-token", 42)
        self.assertIsNotNone(event)
        self.assertIn("Não foi possível iniciar o atendimento", str(event))
        self.assertEqual(state.atendimento_phase, "NO_LOCAL")
        self.assertEqual(state.selected_request["status"], "accepted")
        self.assertEqual(state.available_requests[0]["status"], "accepted")
        self.assertNotIn("private backend detail", "\n".join(captured.output))

    def test_completing_attendance_removes_active_item_and_refreshes_queue(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "atendimento_mock": {"id": 42},
            "atendimento_phase": "ATENDENDO",
            "available_requests": [
                {"id": 42, "is_active": True},
                {"id": 43, "is_active": False},
            ],
            "pending_requests_error": "",
        }.items():
            object.__setattr__(state, name, value)

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch.object(
                OperationalState,
                "_get_auth_identity",
                new=AsyncMock(return_value=("session-token", "provider-1")),
            ),
            patch("sosdrive.complete_service_request_supabase") as complete_request,
            patch("sosdrive.fetch_pending_requests_supabase", return_value=[]),
            patch("sosdrive.fetch_active_service_requests_supabase", return_value=[]),
        ):
            event = asyncio.run(state.advance_atendimento_phase())

        complete_request.assert_called_once_with("session-token", 42)
        self.assertIn("/waiting-payment", str(event))
        self.assertEqual(state.available_requests, [])
        self.assertEqual(state.atendimento_phase, "CONCLUIDO")

    def test_provider_home_header_and_map_recenter_action_overlay_the_map(self):
        screen = provider_home_screen()
        header = screen.children[0]
        map_pane = screen.children[1].children[0]
        map_frame = map_pane.children[0]
        recenter_button = map_frame.children[1]
        rendered = self.render_component(screen)

        self.assertNotEqual(getattr(header, "position", None), "fixed")
        self.assertEqual(map_frame.position, "relative")
        self.assertEqual(recenter_button.position, "absolute")
        self.assertEqual(recenter_button.top, "0.75rem")
        self.assertIn("provider-map-frame", map_frame.class_name)
        self.assertEqual(map_frame.children[0].id, "provider-home-map")
        self.assertIn("window.requestProviderMapLocation('provider-home-map')", rendered)
        self.assertIn("toggle_provider_status", rendered)
        self.assertIn("view_request_details", rendered)
        self.assertIn("provider-request-active-badge", rendered)
        self.assertIn("Em andamento", rendered)

    def test_provider_home_styles_are_global_and_responsive(self):
        mobile_styles = GLOBAL_STYLE["@media only screen and (max-width: 720px)"]

        self.assertIn(".provider-home-page", GLOBAL_STYLE)
        self.assertNotIn(".provider-home-page", GLOBAL_STYLE[".user-home-root"])
        self.assertIn("linear-gradient", GLOBAL_STYLE[".provider-home-page"]["background"])
        self.assertEqual(GLOBAL_STYLE[".provider-home-body"]["height"], "auto")
        self.assertEqual(GLOBAL_STYLE[".provider-map-pane"]["height"], "calc(100vh - 8rem)")
        self.assertEqual(
            GLOBAL_STYLE[".provider-requests-pane"]["overflow_y"],
            "visible",
        )
        self.assertEqual(
            GLOBAL_STYLE[".provider-requests-pane > .rx-Stack"]["height"],
            "auto",
        )
        self.assertEqual(
            mobile_styles[".provider-home-body"]["flex_direction"],
            "column",
        )
        self.assertEqual(
            mobile_styles[".provider-requests-pane"]["overflow_y"],
            "visible",
        )
        self.assertEqual(
            mobile_styles[".provider-requests-pane"]["height"],
            "auto",
        )
        self.assertEqual(
            GLOBAL_STYLE[".provider-map-frame"]["border_radius"],
            "16px",
        )
        self.assertEqual(
            GLOBAL_STYLE[".provider-request-active-badge"]["background"],
            "#FFF7ED",
        )
        self.assertEqual(
            GLOBAL_STYLE[".provider-request-active-badge"]["white_space"],
            "nowrap",
        )

    def test_service_details_layout_preserves_actions_and_leaflet_mount(self):
        rendered = self.render_component(service_details_screen())

        self.assertIn("service-details-card", rendered)
        self.assertIn("service-details-map-card", rendered)
        self.assertIn("service-details-call-button", rendered)
        self.assertIn("service-details-message-button", rendered)
        self.assertIn("service-details-accept-button", rendered)
        self.assertIn("service-details-route-button", rendered)
        self.assertIn("service-end-button", rendered)
        self.assertIn("encerrar_chamado", rendered)
        self.assertIn("accept_request", rendered)
        self.assertIn('id:"service-details-map"', rendered)
        self.assertIn(
            "window.initSOSMap('service-details-map', [-23.5614, -46.6559], 14);",
            inspect.getsource(service_details_screen),
        )
        self.assertIn('"tel:"+', rendered)
        self.assertIn('["maps_url"]', rendered)

    def test_provider_progress_screen_has_active_request_end_action(self):
        rendered = self.render_component(provider_service_progress_screen())

        self.assertIn("service-end-button", rendered)
        self.assertIn("encerrar_chamado", rendered)
        self.assertIn("is_ending_request", rendered)

    def test_service_details_styles_define_responsive_premium_layout(self):
        grid_styles = GLOBAL_STYLE[".service-details-grid"]

        self.assertIn("linear-gradient", GLOBAL_STYLE[".service-details-page"]["background"])
        self.assertIn("24px", GLOBAL_STYLE[".service-details-card"]["border_radius"])
        self.assertEqual(
            grid_styles["@media (max-width: 900px)"]["grid_template_columns"],
            "minmax(0, 1fr)",
        )
        self.assertEqual(
            GLOBAL_STYLE[".service-details-map"]["overflow"],
            "hidden",
        )
        self.assertEqual(
            GLOBAL_STYLE[".service-end-button"]["background"],
            "#FEF2F2",
        )

    def test_end_service_request_keeps_provider_waiting_for_payment(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "is_ending_request": False,
            "atendimento_mock": {"id": 42},
            "selected_request": {"id": 42, "status": "accepted", "is_active": True},
            "available_requests": [{"id": 42}, {"id": 43}],
            "atendimento_phase": "ATENDENDO",
            "show_cancel_confirm": True,
            "show_message_panel": True,
            "service_messages": [{"id": 1}],
            "active_message_request_id": 42,
            "message_poll_generation": 1,
            "message_sync_status": "Enviando",
            "message_error": "erro anterior",
            "message_draft": "mensagem",
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.encerrar_chamado()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch.object(
                OperationalState,
                "_get_auth_identity",
                new=AsyncMock(return_value=("session-token", "provider-1")),
            ),
            patch(
                "sosdrive.complete_service_request_supabase",
                return_value={"id": 42, "status": "completed"},
            ) as complete_request,
            patch("sosdrive.fetch_pending_requests_supabase", return_value=[]),
            patch("sosdrive.fetch_active_service_requests_supabase", return_value=[]),
        ):
            events = asyncio.run(consume())

        complete_request.assert_called_once_with("session-token", 42)
        self.assertIn("/waiting-payment", str(events[-1]))
        self.assertEqual(state.available_requests, [])
        self.assertEqual(
            state.selected_request,
            {"id": 42, "status": "completed", "is_active": False},
        )
        self.assertEqual(state.atendimento_mock, {"id": 42})
        self.assertEqual(state.atendimento_phase, "CONCLUIDO")
        self.assertFalse(state.show_cancel_confirm)
        self.assertFalse(state.show_message_panel)
        self.assertEqual(state.service_messages, [])
        self.assertIsNone(state.active_message_request_id)
        self.assertEqual(state.message_poll_generation, 2)
        self.assertEqual(state.message_draft, "")
        self.assertFalse(state.is_ending_request)

    def test_end_service_request_rejects_pending_request_before_supabase(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "is_ending_request": False,
            "atendimento_mock": {"id": 43},
            "selected_request": {"id": 42, "status": "pending", "is_active": False},
            "atendimento_phase": "A_CAMINHO",
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.encerrar_chamado()]

        with patch("sosdrive.complete_service_request_supabase") as complete_request:
            events = asyncio.run(consume())

        complete_request.assert_not_called()
        self.assertEqual(len(events), 1)
        self.assertIn("Aceite o chamado", str(events[0]))
        self.assertFalse(state.is_ending_request)

    def test_end_service_request_failure_preserves_state_and_reports_error(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "is_ending_request": False,
            "atendimento_mock": {"id": 42},
            "selected_request": {"id": 42, "status": "accepted", "is_active": True},
            "available_requests": [{"id": 42}],
            "atendimento_phase": "A_CAMINHO",
            "show_cancel_confirm": False,
            "show_message_panel": False,
            "service_messages": [],
            "active_message_request_id": None,
            "message_poll_generation": 0,
            "message_sync_status": "",
            "message_error": "",
            "message_draft": "",
        }.items():
            object.__setattr__(state, name, value)

        async def consume():
            return [event async for event in state.encerrar_chamado()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch(
                "sosdrive.complete_service_request_supabase",
                side_effect=SupabaseBackendError(409, "private backend detail"),
            ) as complete_request,
            self.assertLogs("sosdrive", level="ERROR") as captured,
        ):
            events = asyncio.run(consume())

        complete_request.assert_called_once_with("session-token", 42)
        self.assertIsNotNone(events[-1])
        self.assertEqual(state.selected_request["id"], 42)
        self.assertEqual(state.selected_request["status"], "accepted")
        self.assertEqual(state.available_requests, [{"id": 42}])
        self.assertEqual(state.atendimento_phase, "A_CAMINHO")
        self.assertFalse(state.is_ending_request)
        self.assertNotIn("private backend detail", "\n".join(captured.output))

    def test_end_service_request_requires_a_selected_request(self):
        state = OperationalState.__new__(OperationalState)
        object.__setattr__(state, "dirty_vars", set())
        object.__setattr__(state, "is_ending_request", False)
        object.__setattr__(state, "atendimento_mock", {})
        object.__setattr__(state, "selected_request", {})

        async def consume():
            return [event async for event in state.encerrar_chamado()]

        with patch("sosdrive.complete_service_request_supabase") as complete_request:
            events = asyncio.run(consume())

        complete_request.assert_not_called()
        self.assertEqual(len(events), 1)
        self.assertIsNotNone(events[0])
        self.assertFalse(state.is_ending_request)

    def test_end_service_request_expires_auth_session_on_unauthorized_response(self):
        state = OperationalState.__new__(OperationalState)
        for name, value in {
            "dirty_vars": set(),
            "is_ending_request": False,
            "atendimento_mock": {"id": 42},
            "selected_request": {"id": 42, "status": "accepted", "is_active": True},
            "available_requests": [{"id": 42}],
            "atendimento_phase": "A_CAMINHO",
        }.items():
            object.__setattr__(state, name, value)
        auth_state = AuthState.__new__(AuthState)
        object.__setattr__(auth_state, "dirty_vars", set())
        object.__setattr__(auth_state, "session_validated", True)

        async def consume():
            return [event async for event in state.encerrar_chamado()]

        with (
            patch.object(
                OperationalState,
                "_get_auth_token",
                new=AsyncMock(return_value="session-token"),
            ),
            patch.object(
                OperationalState,
                "get_state",
                new=AsyncMock(return_value=auth_state),
            ),
            patch(
                "sosdrive.complete_service_request_supabase",
                side_effect=SupabaseBackendError(401, "private backend detail"),
            ),
            self.assertLogs("sosdrive", level="ERROR"),
        ):
            events = asyncio.run(consume())

        self.assertFalse(auth_state.session_validated)
        self.assertEqual(auth_state.error_message, "Sua sessão expirou. Entre novamente.")
        self.assertIn("/login", str(events[-1]))
        self.assertFalse(state.is_ending_request)

    def test_provider_service_progress_home_button_returns_to_provider_area(self):
        rendered = self.render_component(provider_service_progress_screen())

        self.assertIn("Área do prestador", rendered)
        self.assertIn('["path"] : "/home_provider"', rendered)

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
