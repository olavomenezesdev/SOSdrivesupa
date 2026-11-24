import base64
import struct
import unittest
from unittest.mock import Mock, patch
import os
import zlib

from supabase_backend import (
    SupabaseBackendError,
    create_service_payment,
    fetch_provider_earnings_balance,
    fetch_service_payment_status,
    process_asaas_webhook,
    submit_service_review,
)

CUSTOMER_ID = "80b7e168-befc-42d2-a7f5-f69c966c7876"
PROVIDER_ID = "705664fc-a07b-4dcf-b944-46fbf09924b0"


def _request_client(request_row):
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        request_row
    ]
    auth_user = Mock()
    auth_user.user.id = CUSTOMER_ID
    client.auth.get_user.return_value = auth_user
    return client


class TestServicePayment(unittest.TestCase):
    def setUp(self):
        self.checkout_url_patcher = patch.dict(
            os.environ,
            {"ASAAS_CHECKOUT_RETURN_URL": "https://api.example.com"},
        )
        self.checkout_url_patcher.start()
        self.addCleanup(self.checkout_url_patcher.stop)

    def _payment_status_clients(self, amount="91.06"):
        auth_client = _request_client(
            {
                "id": 123,
                "user_id": CUSTOMER_ID,
                "provider_id": PROVIDER_ID,
                "status": "completed",
            }
        )
        service_client = Mock()
        table = service_client.table.return_value
        table.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
            Mock(
                data=[
                    {
                        "id": 8,
                        "customer_id": CUSTOMER_ID,
                        "status": "pending",
                        "payment_method": "credit_card",
                        "amount": amount,
                        "checkout_url": "https://checkout.example",
                        "gateway_checkout_id": "checkout-91",
                    }
                ]
            ),
            Mock(data=[{"status": "confirmed"}]),
        ]
        return auth_client, service_client

    def test_rejects_invalid_payment_method(self):
        with (
            patch("supabase_backend._authenticated_client") as authenticated_client,
            patch("supabase_backend.requests.post") as asaas_request,
        ):
            for method in ("cash", "pix", "machine"):
                with self.subTest(method=method):
                    with self.assertRaises(SupabaseBackendError) as error:
                        create_service_payment("access-token", 123, method)
                    self.assertEqual(error.exception.status_code, 400)

        authenticated_client.assert_not_called()
        asaas_request.assert_not_called()

    def test_manual_refresh_reconciles_paid_checkout_with_asaas(self):
        auth_client, service_client = self._payment_status_clients()
        asaas_response = Mock(status_code=200)
        asaas_response.json.return_value = {
            "data": [
                {
                    "id": "pay-confirmed-91",
                    "checkoutSession": "checkout-91",
                    "value": 91.06,
                    "status": "RECEIVED",
                }
            ]
        }

        with (
            patch("supabase_backend._authenticated_client", return_value=auth_client),
            patch("supabase_backend._service_client", return_value=service_client),
            patch(
                "supabase_backend._asaas_settings",
                return_value=("private-api-key", "https://api-sandbox.asaas.com/v3"),
            ),
            patch("supabase_backend.requests.get", return_value=asaas_response) as asaas_get,
        ):
            result = fetch_service_payment_status(
                "access-token",
                123,
                reconcile_with_gateway=True,
            )

        asaas_get.assert_called_once_with(
            "https://api-sandbox.asaas.com/v3/payments",
            headers={
                "accept": "application/json",
                "access_token": "private-api-key",
            },
            params={"checkoutSession": "checkout-91", "limit": 10},
            timeout=15,
        )
        service_client.table.return_value.update.assert_called_once_with(
            {
                "status": "confirmed",
                "gateway_payment_id": "pay-confirmed-91",
            }
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertNotIn("id", result)
        self.assertNotIn("gateway_checkout_id", result)

    def test_manual_refresh_keeps_pending_if_asaas_does_not_confirm(self):
        auth_client, service_client = self._payment_status_clients()
        asaas_response = Mock(status_code=200)
        asaas_response.json.return_value = {
            "data": [
                {
                    "id": "pay-pending-91",
                    "checkoutSession": "checkout-91",
                    "value": 91.06,
                    "status": "PENDING",
                }
            ]
        }

        with (
            patch("supabase_backend._authenticated_client", return_value=auth_client),
            patch("supabase_backend._service_client", return_value=service_client),
            patch(
                "supabase_backend._asaas_settings",
                return_value=("private-api-key", "https://api-sandbox.asaas.com/v3"),
            ),
            patch("supabase_backend.requests.get", return_value=asaas_response),
        ):
            result = fetch_service_payment_status(
                "access-token",
                123,
                reconcile_with_gateway=True,
            )

        service_client.table.return_value.update.assert_not_called()
        self.assertEqual(result["status"], "pending")

    def test_manual_refresh_does_not_confirm_ambiguous_or_mismatched_results(self):
        scenarios = (
            (
                "ambiguous",
                [
                    {
                        "id": "pay-1",
                        "checkoutSession": "checkout-91",
                        "value": 91.06,
                        "status": "RECEIVED",
                    },
                    {
                        "id": "pay-2",
                        "checkoutSession": "checkout-91",
                        "value": 91.06,
                        "status": "RECEIVED",
                    },
                ],
            ),
            (
                "wrong-amount",
                [
                    {
                        "id": "pay-1",
                        "checkoutSession": "checkout-91",
                        "value": 91.07,
                        "status": "RECEIVED",
                    }
                ],
            ),
            (
                "wrong-checkout",
                [
                    {
                        "id": "pay-1",
                        "checkoutSession": "different-checkout",
                        "value": 91.06,
                        "status": "RECEIVED",
                    }
                ],
            ),
        )
        for scenario, data in scenarios:
            with self.subTest(scenario=scenario):
                auth_client, service_client = self._payment_status_clients()
                asaas_response = Mock(status_code=200)
                asaas_response.json.return_value = {"data": data}
                with (
                    patch("supabase_backend._authenticated_client", return_value=auth_client),
                    patch("supabase_backend._service_client", return_value=service_client),
                    patch(
                        "supabase_backend._asaas_settings",
                        return_value=("private-api-key", "https://api-sandbox.asaas.com/v3"),
                    ),
                    patch("supabase_backend.requests.get", return_value=asaas_response),
                ):
                    result = fetch_service_payment_status(
                        "access-token",
                        123,
                        reconcile_with_gateway=True,
                    )

                service_client.table.return_value.update.assert_not_called()
                self.assertEqual(result["status"], "pending")

    def test_creates_hosted_checkout_with_server_amount(self):
        request_row = {
            "id": 123,
            "user_id": CUSTOMER_ID,
            "provider_id": PROVIDER_ID,
            "estimated_price": "57.84",
            "status": "completed",
        }
        client = _request_client(request_row)
        service_client = Mock()
        service_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        response = Mock(status_code=200)
        response.json.return_value = {
            "id": "checkout-123",
            "link": "https://sandbox.asaas.com/checkoutSession/show/checkout-123",
        }

        with (
            patch("supabase_backend._authenticated_client", return_value=client),
            patch("supabase_backend._service_client", return_value=service_client),
            patch("supabase_backend._asaas_settings", return_value=("api-key", "https://api-sandbox.asaas.com/v3")),
            patch("supabase_backend.requests.post", return_value=response) as asaas_request,
        ):
            result = create_service_payment("access-token", 123, "credit_card")

        payload = asaas_request.call_args.kwargs["json"]
        self.assertEqual(payload["billingTypes"], ["CREDIT_CARD"])
        self.assertEqual(payload["items"][0]["value"], 57.84)
        self.assertEqual(
            payload["callback"],
            {
                "successUrl": "https://api.example.com/api/asaas/checkout-return/success",
                "cancelUrl": "https://api.example.com/api/asaas/checkout-return/cancel",
                "expiredUrl": "https://api.example.com/api/asaas/checkout-return/expired",
            },
        )
        image = base64.b64decode(payload["items"][0]["imageBase64"], validate=True)
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        offset = 8
        while offset < len(image):
            length = struct.unpack(">I", image[offset : offset + 4])[0]
            chunk = image[offset + 4 : offset + 8 + length]
            expected_crc = struct.unpack(
                ">I",
                image[offset + 8 + length : offset + 12 + length],
            )[0]
            self.assertEqual(zlib.crc32(chunk) & 0xFFFFFFFF, expected_crc)
            offset += 12 + length
        self.assertNotIn("creditCard", payload)
        self.assertNotIn("creditCardHolderInfo", payload)
        self.assertEqual(result["checkout_url"], response.json.return_value["link"])

    def test_completed_status_is_required(self):
        request_row = {
            "id": 123,
            "user_id": CUSTOMER_ID,
            "provider_id": PROVIDER_ID,
            "estimated_price": "57.84",
            "status": "in_progress",
        }
        client = _request_client(request_row)
        with patch("supabase_backend._authenticated_client", return_value=client):
            with self.assertRaises(SupabaseBackendError) as error:
                create_service_payment("access-token", 123, "credit_card")
        self.assertEqual(error.exception.status_code, 409)

    def test_localhost_is_rejected_as_checkout_callback_origin(self):
        request_row = {
            "id": 123,
            "user_id": CUSTOMER_ID,
            "provider_id": PROVIDER_ID,
            "estimated_price": "57.84",
            "status": "completed",
        }
        client = _request_client(request_row)
        with (
            patch.dict(os.environ, {"ASAAS_CHECKOUT_RETURN_URL": "http://localhost:3000"}),
            patch("supabase_backend._authenticated_client", return_value=client),
            patch("supabase_backend._service_client"),
            patch("supabase_backend._asaas_settings", return_value=("api-key", "https://api-sandbox.asaas.com/v3")),
            patch("supabase_backend.requests.post") as asaas_request,
            self.assertRaises(SupabaseBackendError) as error,
        ):
            create_service_payment("access-token", 123, "credit_card")

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("public HTTPS origin", error.exception.message)
        asaas_request.assert_not_called()

    def test_asaas_bad_request_exposes_only_error_codes(self):
        request_row = {
            "id": 123,
            "user_id": CUSTOMER_ID,
            "provider_id": PROVIDER_ID,
            "estimated_price": "57.84",
            "status": "completed",
        }
        client = _request_client(request_row)
        service_client = Mock()
        service_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        response = Mock(status_code=400)
        response.json.return_value = {
            "errors": [
                {
                    "code": "invalid_checkout",
                    "description": "Rejected payload containing private customer data",
                },
                {"code": "invalid_checkout", "description": "duplicate code"},
                {"description": "error without a code"},
                {"code": "bad code", "description": "unsafe code"},
            ]
        }

        with (
            patch("supabase_backend._authenticated_client", return_value=client),
            patch("supabase_backend._service_client", return_value=service_client),
            patch(
                "supabase_backend._asaas_settings",
                return_value=("api-key", "https://api-sandbox.asaas.com/v3"),
            ),
            patch("supabase_backend.requests.post", return_value=response),
            self.assertLogs("supabase_backend", level="ERROR") as captured,
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            create_service_payment("access-token", 123, "credit_card")

        self.assertIn("error_codes=invalid_checkout", raised.exception.message)
        log_output = "\n".join(captured.output)
        self.assertIn("invalid_checkout", log_output)
        self.assertNotIn("private customer data", log_output)
        self.assertNotIn("unsafe code", log_output)

    def test_asaas_error_details_are_useful_and_redact_sensitive_values(self):
        request_row = {
            "id": 123,
            "user_id": CUSTOMER_ID,
            "provider_id": PROVIDER_ID,
            "estimated_price": "57.84",
            "status": "completed",
        }
        client = _request_client(request_row)
        service_client = Mock()
        service_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        response = Mock(status_code=400)
        response.json.return_value = {
            "errors": [
                {
                    "code": "invalid_object",
                    "description": (
                        "Callback URL http://localhost:3000/payment invalid for "
                        "test@example.com number 12345678901"
                    ),
                }
            ]
        }

        with (
            patch("supabase_backend._authenticated_client", return_value=client),
            patch("supabase_backend._service_client", return_value=service_client),
            patch(
                "supabase_backend._asaas_settings",
                return_value=("api-key", "https://api-sandbox.asaas.com/v3"),
            ),
            patch("supabase_backend.requests.post", return_value=response),
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            create_service_payment("access-token", 123, "credit_card")

        self.assertIn("Callback URL [URL] invalid", raised.exception.message)
        self.assertIn("[email]", raised.exception.message)
        self.assertIn("[number]", raised.exception.message)
        self.assertNotIn("test@example.com", raised.exception.message)
        self.assertNotIn("12345678901", raised.exception.message)


class TestAsaasWebhook(unittest.TestCase):
    def test_created_event_does_not_confirm_payment(self):
        with patch.dict(os.environ, {"ASAAS_WEBHOOK_TOKEN": "webhook-secret"}):
            result = process_asaas_webhook(
                {"event": "PAYMENT_CREATED", "payment": {"id": "pay-1"}},
                "webhook-secret",
            )
        self.assertEqual(result, {"processed": False, "reason": "event_ignored"})

    def test_checkout_paid_confirms_payment_idempotently(self):
        service_client = Mock()
        service_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"id": 42, "status": "pending"}
        ]
        with (
            patch.dict(os.environ, {"ASAAS_WEBHOOK_TOKEN": "webhook-secret"}),
            patch("supabase_backend._service_client", return_value=service_client),
        ):
            result = process_asaas_webhook(
                {"event": "CHECKOUT_PAID", "checkout": {"id": "checkout-1"}},
                "webhook-secret",
            )

        self.assertTrue(result["processed"])
        self.assertFalse(result["duplicate"])
        update = service_client.table.return_value.update.call_args.args[0]
        self.assertEqual(update["status"], "confirmed")


class TestProviderEarnings(unittest.TestCase):
    def test_provider_can_only_fetch_own_confirmed_earnings(self):
        auth_client = _request_client({})
        auth_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"id": CUSTOMER_ID, "role": "prestador"}
        ]
        service_client = Mock()
        service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"amount": "91.06"},
            {"amount": "25.40"},
        ]

        with (
            patch("supabase_backend._authenticated_client", return_value=auth_client),
            patch("supabase_backend._service_client", return_value=service_client),
        ):
            result = fetch_provider_earnings_balance("access-token")

        service_client.table.assert_called_once_with("provider_earnings")
        service_client.table.return_value.select.assert_called_once_with("amount")
        service_client.table.return_value.select.return_value.eq.assert_called_once_with(
            "provider_id",
            CUSTOMER_ID,
        )
        self.assertAlmostEqual(result["balance"], 116.46)
        self.assertEqual(result["count"], 2)

    def test_customer_cannot_fetch_provider_earnings(self):
        auth_client = _request_client({})
        auth_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"id": CUSTOMER_ID, "role": "cliente"}
        ]
        with (
            patch("supabase_backend._authenticated_client", return_value=auth_client),
            patch("supabase_backend._service_client") as service_client,
            self.assertRaises(SupabaseBackendError) as raised,
        ):
            fetch_provider_earnings_balance("access-token")

        self.assertEqual(raised.exception.status_code, 403)
        service_client.assert_not_called()


class TestServiceReviews(unittest.TestCase):
    def test_review_requires_confirmed_payment_and_inserts_as_service_role(self):
        auth_client = _request_client(
            {
                "id": 123,
                "user_id": CUSTOMER_ID,
                "provider_id": PROVIDER_ID,
                "status": "completed",
            }
        )
        request_table = Mock()
        request_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": 123,
                "user_id": CUSTOMER_ID,
                "provider_id": PROVIDER_ID,
                "status": "completed",
            }
        ]
        payment_table = Mock()
        payment_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"status": "confirmed"}
        ]
        review_table = Mock()
        review_table.insert.return_value.execute.return_value.data = [
            {"id": 7, "rating": 5}
        ]
        service_client = Mock()
        service_client.table.side_effect = lambda name: {
            "service_request_payments": payment_table,
            "service_request_reviews": review_table,
        }[name]
        auth_client.table.return_value = request_table

        with (
            patch("supabase_backend._authenticated_client", return_value=auth_client),
            patch("supabase_backend._service_client", return_value=service_client),
        ):
            result = submit_service_review("access-token", 123, 5, "Ótimo atendimento")

        self.assertEqual(result["rating"], 5)
        review_table.insert.assert_called_once()
        review_row = review_table.insert.call_args.args[0]
        self.assertEqual(review_row["reviewer_id"], CUSTOMER_ID)
        self.assertEqual(review_row["reviewee_id"], PROVIDER_ID)

    def test_review_is_rejected_when_payment_is_pending(self):
        request_table = Mock()
        request_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": 123,
                "user_id": CUSTOMER_ID,
                "provider_id": PROVIDER_ID,
                "status": "completed",
            }
        ]
        auth_client = _request_client(
            {
                "id": 123,
                "user_id": CUSTOMER_ID,
                "provider_id": PROVIDER_ID,
                "status": "completed",
            }
        )
        auth_client.table.return_value = request_table
        payment_table = Mock()
        payment_table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"status": "pending"}
        ]
        service_client = Mock()
        service_client.table.return_value = payment_table

        with (
            patch("supabase_backend._authenticated_client", return_value=auth_client),
            patch("supabase_backend._service_client", return_value=service_client),
        ):
            with self.assertRaises(SupabaseBackendError) as error:
                submit_service_review("access-token", 123, 4, "")

        self.assertEqual(error.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
