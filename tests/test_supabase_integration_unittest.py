import base64
import hashlib
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import psycopg
import requests
from postgrest.exceptions import APIError
from supabase import create_client

from supabase_backend import (
    SupabaseBackendError,
    accept_service_request,
    cancel_service_request,
    complete_service_request,
    create_service_request,
    delete_profile_photo,
    fetch_pending_requests,
    fetch_service_messages,
    fetch_service_request,
    fetch_user_vehicles,
    get_profile,
    release_service_request,
    save_profile,
    save_vehicle,
    send_service_message,
    sign_in,
    signed_profile_photo_url,
    start_service_request,
    upload_profile_photo,
)
from supabase_config import get_supabase_settings


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/"
    "iZk9HQAAAABJRU5ErkJggg=="
)


@unittest.skipUnless(
    os.getenv("SUPABASE_TEST_DISPOSABLE_PROJECT", "").strip().lower() == "true",
    "set SUPABASE_TEST_DISPOSABLE_PROJECT=true to authorize disposable Supabase writes",
)
class TestSupabaseDisposableProject(unittest.TestCase):
    def setUp(self):
        self.settings = get_supabase_settings(
            require_service_role=True,
            require_database=True,
        )
        if self.settings.service_role_key is None or self.settings.database_url is None:
            self.fail("Supabase admin and database settings are required for this test")
        self.admin = create_client(self.settings.url, self.settings.service_role_key)
        self.run_id = uuid4().hex
        self.users: dict[str, UUID] = {}
        self.emails: set[str] = set()
        self.sessions = {}
        self.request_ids: set[int] = set()
        self.photo_paths: set[str] = set()

    def tearDown(self):
        cleanup_errors = []
        user_ids = list(self.users.values())
        request_ids = list(self.request_ids)

        if self.photo_paths:
            try:
                with psycopg.connect(self.settings.database_url, connect_timeout=15) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            select name from storage.objects
                            where bucket_id = 'profile-photos' and name = any(%s)
                            """,
                            (list(self.photo_paths),),
                        )
                        existing_photo_paths = [row[0] for row in cursor.fetchall()]
                if existing_photo_paths:
                    self.admin.storage.from_("profile-photos").remove(existing_photo_paths)
            except Exception as error:
                cleanup_errors.append(f"Storage cleanup: {type(error).__name__}")

        if user_ids:
            try:
                with psycopg.connect(self.settings.database_url, connect_timeout=15) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            delete from public.service_messages
                            where sender_id = any(%s::uuid[])
                               or service_request_id = any(%s::bigint[])
                            """,
                            (user_ids, request_ids),
                        )
                        cursor.execute(
                            """
                            delete from public.service_request_acceptance
                            where provider_id = any(%s::uuid[])
                               or service_request_id = any(%s::bigint[])
                            """,
                            (user_ids, request_ids),
                        )
                        cursor.execute(
                            """
                            delete from public.event_log
                            where user_id = any(%s::uuid[])
                            """,
                            (user_ids,),
                        )
                        cursor.execute(
                            """
                            delete from public.service_requests
                            where id = any(%s::bigint[])
                               or user_id = any(%s::uuid[])
                               or provider_id = any(%s::uuid[])
                            """,
                            (request_ids, user_ids, user_ids),
                        )
                        cursor.execute(
                            "delete from public.vehicles where user_id = any(%s::uuid[])",
                            (user_ids,),
                        )
                        cursor.execute(
                            "delete from public.profiles where id = any(%s::uuid[])",
                            (user_ids,),
                        )
            except Exception as error:
                cleanup_errors.append(f"Database cleanup: {type(error).__name__}")

        for user_id in user_ids:
            try:
                self.admin.auth.admin.delete_user(str(user_id))
            except Exception as error:
                cleanup_errors.append(f"Auth cleanup: {type(error).__name__}")

        if user_ids or request_ids or self.photo_paths:
            try:
                with psycopg.connect(self.settings.database_url, connect_timeout=15) as connection:
                    with connection.cursor() as cursor:
                        for table, query, values in (
                            ("profiles", "select count(*) from public.profiles where id = any(%s::uuid[])", (user_ids,)),
                            ("vehicles", "select count(*) from public.vehicles where user_id = any(%s::uuid[])", (user_ids,)),
                            ("requests", "select count(*) from public.service_requests where id = any(%s::bigint[]) or user_id = any(%s::uuid[]) or provider_id = any(%s::uuid[])", (request_ids, user_ids, user_ids)),
                            ("messages", "select count(*) from public.service_messages where sender_id = any(%s::uuid[]) or service_request_id = any(%s::bigint[])", (user_ids, request_ids)),
                            ("acceptances", "select count(*) from public.service_request_acceptance where provider_id = any(%s::uuid[]) or service_request_id = any(%s::bigint[])", (user_ids, request_ids)),
                            ("events", "select count(*) from public.event_log where user_id = any(%s::uuid[])", (user_ids,)),
                            ("auth users", "select count(*) from auth.users where id = any(%s::uuid[])", (user_ids,)),
                        ):
                            cursor.execute(query, values)
                            if cursor.fetchone()[0]:
                                cleanup_errors.append(f"Remaining test rows in {table}")
                        if self.photo_paths:
                            cursor.execute(
                                """
                                select count(*) from storage.objects
                                where bucket_id = 'profile-photos' and name = any(%s)
                                """,
                                (list(self.photo_paths),),
                            )
                            if cursor.fetchone()[0]:
                                cleanup_errors.append("Remaining test profile photos")
            except Exception as error:
                cleanup_errors.append(f"Cleanup verification: {type(error).__name__}")

        if self.admin._storage is not None:
            self.admin._storage.session.close()
        self.admin.auth.close()
        if cleanup_errors:
            self.fail("Disposable test cleanup incomplete: " + ", ".join(cleanup_errors))

    def _assert_application_data_empty(self):
        tables = (
            "profiles",
            "vehicles",
            "service_requests",
            "service_request_acceptance",
            "service_messages",
            "event_log",
        )
        with psycopg.connect(self.settings.database_url, connect_timeout=15) as connection:
            with connection.cursor() as cursor:
                cursor.execute("set transaction read only")
                for table in tables:
                    cursor.execute(f"select count(*) from public.{table}")
                    self.assertEqual(
                        cursor.fetchone()[0],
                        0,
                        f"Refusing disposable tests because public.{table} is not empty",
                    )
                cursor.execute(
                    "select count(*) from storage.objects where bucket_id = 'profile-photos'"
                )
                self.assertEqual(
                    cursor.fetchone()[0],
                    0,
                    "Refusing disposable tests because profile-photos is not empty",
                )

    def test_owner_authorization_request_concurrency_chat_storage_and_cleanup(self):
        self._assert_application_data_empty()

        # Create users with passwords retained only in this test process.
        credentials = {}
        for role in ("cliente", "prestador_a", "prestador_b", "nao_participante"):
            role_value = "cliente" if role in {"cliente", "nao_participante"} else "prestador"
            email = f"sosdrive-{self.run_id}-{role}@example.com"
            password = f"SosDrive-{uuid4().hex}-Aa9!"
            response = self.admin.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "name": f"Disposable {role}",
                        "role": role_value,
                    },
                }
            )
            self.users[role] = UUID(str(response.user.id))
            credentials[role] = (email, password)

        for role, (email, password) in credentials.items():
            self.sessions[role] = sign_in(email, password)
            expected_role = "cliente" if role in {"cliente", "nao_participante"} else "prestador"
            self.assertEqual(self.sessions[role].user["role"], expected_role)

        client = self.sessions["cliente"]
        provider_a = self.sessions["prestador_a"]
        provider_b = self.sessions["prestador_b"]
        outsider = self.sessions["nao_participante"]

        profile = get_profile(client.access_token, client.refresh_token)
        self.assertEqual(profile["id"], str(self.users["cliente"]))
        saved_profile = save_profile(
            client.access_token,
            {
                "nome_completo": "Disposable Client",
                "cpf": "",
                "telefone": "",
                "foto_perfil": "",
            },
            client.refresh_token,
        )
        self.assertEqual(saved_profile["nome_completo"], "Disposable Client")

        vehicle = save_vehicle(
            client.access_token,
            {
                "brand": "Test",
                "model": "Disposable",
                "plate": f"T{self.run_id[:6].upper()}",
                "year": 2020,
                "color": "Blue",
            },
        )
        vehicle_id = int(vehicle["id"])
        self.assertEqual(len(fetch_user_vehicles(client.access_token)), 1)
        self.assertEqual(fetch_user_vehicles(provider_a.access_token), [])

        outsider_api = create_client(self.settings.url, self.settings.anon_key)
        outsider_api.postgrest.auth(outsider.access_token)
        try:
            denied_profile_update = (
                outsider_api.table("profiles")
                .update({"full_name": "Unauthorized update"})
                .eq("id", str(self.users["cliente"]))
                .execute()
                .data
            )
            self.assertEqual(denied_profile_update, [])
            denied_vehicle_update = (
                outsider_api.table("vehicles")
                .update({"color": "Unauthorized update"})
                .eq("id", vehicle_id)
                .execute()
                .data
            )
            self.assertEqual(denied_vehicle_update, [])
        finally:
            outsider_api.auth.close()
            if outsider_api._postgrest is not None:
                outsider_api._postgrest.aclose()
            if outsider_api._storage is not None:
                outsider_api._storage.session.close()

        self.assertEqual(get_profile(client.access_token)["full_name"], "Disposable Client")
        self.assertEqual(fetch_user_vehicles(client.access_token)[0]["color"], "Blue")

        with self.assertRaises(SupabaseBackendError) as client_queue_error:
            fetch_pending_requests(client.access_token)
        self.assertEqual(client_queue_error.exception.status_code, 403)

        with self.assertRaises(SupabaseBackendError) as wrong_owner_error:
            create_service_request(
                outsider.access_token,
                "tire",
                vehicle_id,
                -23.55,
                -46.63,
            )
        self.assertEqual(wrong_owner_error.exception.status_code, 403)

        request = create_service_request(
            client.access_token,
            "tire",
            vehicle_id,
            -23.55,
            -46.63,
        )
        request_id = int(request["request_id"])
        self.request_ids.add(request_id)
        self.assertEqual(request["status"], "pending")
        pending = fetch_pending_requests(provider_a.access_token)
        self.assertTrue(any(int(row["id"]) == request_id for row in pending))

        outsider_api = create_client(self.settings.url, self.settings.anon_key)
        outsider_api.postgrest.auth(outsider.access_token)
        try:
            with self.assertRaises(APIError) as spoofed_author_error:
                (
                    outsider_api.table("service_messages")
                    .insert(
                        {
                            "service_request_id": request_id,
                            "sender_id": str(self.users["cliente"]),
                            "message_text": "Unauthorized spoof",
                        }
                    )
                    .execute()
                )
            self.assertEqual(spoofed_author_error.exception.code, "42501")
        finally:
            outsider_api.auth.close()
            if outsider_api._postgrest is not None:
                outsider_api._postgrest.aclose()
            if outsider_api._storage is not None:
                outsider_api._storage.session.close()

        def attempt_accept(session):
            try:
                return accept_service_request(session.access_token, request_id)
            except SupabaseBackendError as error:
                cause = error.__cause__
                return (
                    error.status_code,
                    getattr(cause, "code", None),
                    type(cause).__name__ if cause is not None else None,
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt_accept, (provider_a, provider_b)))
        successful = [result for result in results if isinstance(result, dict)]
        rejected = [result for result in results if not isinstance(result, dict)]
        self.assertEqual(len(successful), 1)
        winner_id = str(successful[0]["provider_id"])
        winner = provider_a if str(self.users["prestador_a"]) == winner_id else provider_b
        other_provider = provider_b if winner is provider_a else provider_a
        self.assertEqual(rejected[0][0], 409, f"Unexpected losing acceptance result: {rejected}")

        with self.assertRaises(SupabaseBackendError) as client_accept_error:
            accept_service_request(client.access_token, request_id)
        self.assertEqual(client_accept_error.exception.status_code, 403)
        self.assertIsNone(fetch_service_request(outsider.access_token, request_id))

        send_service_message(client.access_token, request_id, "Mensagem descartável do cliente")
        send_service_message(winner.access_token, request_id, "Mensagem descartável do prestador")
        messages = fetch_service_messages(client.access_token, request_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(fetch_service_messages(outsider.access_token, request_id), [])
        with self.assertRaises(SupabaseBackendError) as outsider_message_error:
            send_service_message(outsider.access_token, request_id, "Não autorizado")
        self.assertEqual(outsider_message_error.exception.status_code, 403)

        with self.assertRaises(SupabaseBackendError) as client_start_error:
            start_service_request(client.access_token, request_id)
        self.assertEqual(client_start_error.exception.status_code, 403)
        with self.assertRaises(SupabaseBackendError) as unassigned_start_error:
            start_service_request(other_provider.access_token, request_id)
        self.assertEqual(unassigned_start_error.exception.status_code, 403)

        started = start_service_request(winner.access_token, request_id)
        self.assertEqual(started["status"], "in_progress")
        repeated_start = start_service_request(winner.access_token, request_id)
        self.assertEqual(repeated_start["status"], "in_progress")
        self.assertEqual(
            fetch_service_request(client.access_token, request_id)["status"],
            "in_progress",
        )

        released = release_service_request(winner.access_token, request_id)
        self.assertEqual(released["status"], "pending")
        reassigned = accept_service_request(other_provider.access_token, request_id)
        self.assertEqual(str(reassigned["provider_id"]), str(self.users["prestador_a"] if other_provider is provider_a else self.users["prestador_b"]))
        started_after_reassignment = start_service_request(
            other_provider.access_token,
            request_id,
        )
        self.assertEqual(started_after_reassignment["status"], "in_progress")
        completed = complete_service_request(other_provider.access_token, request_id)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(fetch_service_request(client.access_token, request_id)["status"], "completed")

        cancelled_request = create_service_request(
            client.access_token,
            "battery",
            vehicle_id,
            -23.55,
            -46.63,
        )
        cancelled_id = int(cancelled_request["request_id"])
        self.request_ids.add(cancelled_id)
        with self.assertRaises(SupabaseBackendError) as provider_cancel_error:
            cancel_service_request(provider_a.access_token, cancelled_id)
        self.assertEqual(provider_cancel_error.exception.status_code, 403)
        cancelled = cancel_service_request(client.access_token, cancelled_id)
        self.assertEqual(cancelled["status"], "cancelled")

        with self.assertRaises(ValueError):
            upload_profile_photo(
                client.access_token,
                client.refresh_token,
                {"mime_type": "image/gif", "content": b"gif"},
                str(self.users["cliente"]),
            )
        with self.assertRaises(ValueError):
            upload_profile_photo(
                client.access_token,
                client.refresh_token,
                {"mime_type": "image/png", "content": b"x" * (5 * 1024 * 1024 + 1)},
                str(self.users["cliente"]),
            )

        photo_path = f"profiles/{self.users['cliente']}/avatar.png"
        self.photo_paths.add(photo_path)
        uploaded_path = upload_profile_photo(
            client.access_token,
            client.refresh_token,
            {
                "name": "avatar.png",
                "mime_type": "image/png",
                "content": PNG_BYTES,
            },
            str(self.users["cliente"]),
        )
        self.assertEqual(uploaded_path, photo_path)
        photo_profile = save_profile(
            client.access_token,
            {
                "nome_completo": "Disposable Client",
                "cpf": "",
                "telefone": "",
                "foto_perfil": photo_path,
            },
            client.refresh_token,
        )
        signed_url = photo_profile["foto_perfil"]
        self.assertTrue(signed_url)
        with self.assertRaises(SupabaseBackendError):
            signed_profile_photo_url(
                outsider.access_token,
                photo_path,
                outsider.refresh_token,
            )

        with requests.get(signed_url, timeout=15) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                hashlib.sha256(response.content).digest(),
                hashlib.sha256(PNG_BYTES).digest(),
            )

        delete_profile_photo(
            outsider.access_token,
            outsider.refresh_token,
            photo_path,
        )
        owner_profile = get_profile(client.access_token, client.refresh_token)
        self.assertEqual(owner_profile["foto_perfil_path"], photo_path)
        owner_photo_url = owner_profile["foto_perfil"]
        with requests.get(owner_photo_url, timeout=15) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(hashlib.sha256(response.content).digest(), hashlib.sha256(PNG_BYTES).digest())

        delete_profile_photo(client.access_token, client.refresh_token, photo_path)
        cleared_profile = save_profile(
            client.access_token,
            {
                "nome_completo": "Disposable Client",
                "cpf": "",
                "telefone": "",
                "foto_perfil": "",
            },
            client.refresh_token,
        )
        self.assertEqual(cleared_profile["foto_perfil_path"], "")


if __name__ == "__main__":
    unittest.main()
