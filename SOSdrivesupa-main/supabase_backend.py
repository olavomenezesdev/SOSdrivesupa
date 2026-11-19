"""User-scoped Supabase operations for the Reflex application."""

from __future__ import annotations

import logging

from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from urllib.parse import urljoin
from uuid import uuid4

import httpx
from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from supabase_config import (
    SupabaseConfigurationError,
    SupabaseSettings,
    get_supabase_email_redirect_url,
    get_supabase_settings,
)


class SupabaseBackendError(RuntimeError):
    """A safe, structured error from Supabase Auth, PostgREST, or Storage."""

    def __init__(self, status_code: int, message: str = "Supabase request failed"):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class SupabaseAuthenticationError(SupabaseBackendError):
    """Authentication was rejected or the authenticated profile is unavailable."""


class SupabaseConfigurationRuntimeError(SupabaseBackendError):
    """Supabase runtime settings are missing or invalid."""


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SupabaseSession:
    access_token: str
    refresh_token: str
    user: dict[str, Any]

P = ParamSpec("P")
R = TypeVar("R")
_OPEN_CLIENTS: ContextVar[list[Client] | None] = ContextVar(
    "supabase_open_clients",
    default=None,
)


def _close_client(client: Client) -> None:
    client.auth.close()
    if client._postgrest is not None:
        client._postgrest.aclose()
    if client._storage is not None:
        client._storage.session.close()
    if client._functions is not None:
        client._functions.session.close()


def _manage_clients(operation: Callable[P, R]) -> Callable[P, R]:
    @wraps(operation)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        clients: list[Client] = []
        context_token = _OPEN_CLIENTS.set(clients)
        try:
            return operation(*args, **kwargs)
        finally:
            _OPEN_CLIENTS.reset(context_token)
            for client in reversed(clients):
                _close_client(client)

    return wrapper


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _status(error: Exception) -> int:
    if isinstance(error, httpx.TimeoutException):
        return 504
    if isinstance(error, httpx.TransportError):
        return 503
    status = getattr(error, "status", None) or getattr(error, "status_code", None)
    try:
        if status is not None:
            return int(status)
    except (TypeError, ValueError):
        pass
    return {
        "PGRST301": 401,
        "42501": 403,
        "40001": 409,
        "22023": 400,
        "23505": 409,
    }.get(str(getattr(error, "code", "")), 500)


def _translate_error(error: Exception) -> SupabaseBackendError:
    status = _status(error)
    if status in {400, 401, 403}:
        return SupabaseAuthenticationError(status, "Supabase authentication or authorization failed")
    return SupabaseBackendError(status)


def _auth_error_code(error: Exception) -> str:
    code = getattr(error, "code", "")
    return code.strip().lower() if isinstance(code, str) else ""


def _settings() -> SupabaseSettings:
    try:
        return get_supabase_settings()
    except RuntimeError as error:
        raise SupabaseConfigurationRuntimeError(503, "Supabase is not configured") from error


def _email_redirect_to() -> str:
    try:
        return get_supabase_email_redirect_url()
    except SupabaseConfigurationError as error:
        raise SupabaseConfigurationRuntimeError(
            503,
            "Email confirmation redirect is not configured",
        ) from error


def _client(settings: SupabaseSettings | None = None) -> Client:
    current = settings or _settings()
    try:
        client = create_client(
            current.url,
            current.anon_key,
            SyncClientOptions(
                postgrest_client_timeout=15,
                storage_client_timeout=15,
                function_client_timeout=15,
            ),
        )
    except Exception as error:
        raise _translate_error(error) from error
    open_clients = _OPEN_CLIENTS.get()
    if open_clients is not None:
        open_clients.append(client)
    return client


def _authenticated_client(access_token: str) -> Client:
    if not access_token.strip():
        raise SupabaseAuthenticationError(401, "Authentication is required")
    client = _client()
    client.postgrest.auth(access_token)
    return client


def _profile_row(client: Client, user_id: str) -> dict[str, Any]:
    try:
        rows = client.table("profiles").select("*").eq("id", user_id).limit(1).execute().data
    except Exception as error:
        raise _translate_error(error) from error
    if not isinstance(rows, list) or not rows:
        raise SupabaseAuthenticationError(401, "Authenticated profile is unavailable")
    profile = rows[0]
    if not isinstance(profile, dict):
        raise SupabaseBackendError(500, "Supabase returned an invalid profile")
    return profile


def _application_user(client: Client, auth_user: Any) -> dict[str, Any]:
    user_id = str(_field(auth_user, "id", "") or "")
    if not user_id:
        raise SupabaseAuthenticationError(401, "Supabase returned an invalid identity")
    profile = _profile_row(client, user_id)
    metadata = _field(auth_user, "user_metadata", {}) or {}
    return {
        "id": user_id,
        "email": _field(auth_user, "email", "") or "",
        "name": profile.get("full_name") or metadata.get("name") or "",
        "role": profile.get("role"),
        "full_name": profile.get("full_name") or "",
        "cpf": profile.get("cpf") or "",
        "telefone": profile.get("telefone") or "",
        "foto_perfil": profile.get("foto_perfil") or "",
    }


def _session_from_response(response: Any) -> SupabaseSession | None:
    session = _field(response, "session")
    if session is None:
        return None
    access_token = str(_field(session, "access_token", "") or "")
    refresh_token = str(_field(session, "refresh_token", "") or "")
    auth_user = _field(response, "user") or _field(session, "user")
    if not access_token or not refresh_token or auth_user is None:
        raise SupabaseBackendError(502, "Supabase returned an incomplete session")
    client = _client()
    client.postgrest.auth(access_token)
    user = _application_user(client, auth_user)
    return SupabaseSession(access_token, refresh_token, user)


@_manage_clients
def sign_up(email: str, password: str, name: str, role: str) -> SupabaseSession | None:
    client = _client()
    try:
        redirect_to = _email_redirect_to()
        response = client.auth.sign_up(
            {
                "email": email.strip().lower(),
                "password": password,
                "options": {
                    "data": {"name": name.strip(), "role": role},
                    "email_redirect_to": redirect_to,
                },
            }
        )
        return _session_from_response(response)
    except Exception as error:
        if isinstance(error, SupabaseBackendError):
            raise
        status = _status(error)
        code = _auth_error_code(error)
        if status == 409 or code in {"user_already_exists", "user_already_registered"}:
            raise SupabaseBackendError(409, "This email is already registered") from error
        if status == 400:
            raise SupabaseBackendError(
                400,
                "Supabase rejected the signup data or Auth configuration",
            ) from error
        raise _translate_error(error) from error


@_manage_clients
def resend_signup_confirmation(email: str) -> None:
    client = _client()
    try:
        client.auth.resend(
            {
                "type": "signup",
                "email": email.strip().lower(),
                "options": {"email_redirect_to": _email_redirect_to()},
            }
        )
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def sign_in(email: str, password: str) -> SupabaseSession:
    client = _client()
    try:
        response = client.auth.sign_in_with_password(
            {"email": email.strip().lower(), "password": password}
        )
        session = _session_from_response(response)
        if session is None:
            raise SupabaseAuthenticationError(401, "Supabase did not return an authenticated session")
        return session
    except SupabaseBackendError:
        raise
    except Exception as error:
        status = _status(error)
        code = _auth_error_code(error)
        if code == "email_not_confirmed":
            raise SupabaseAuthenticationError(
                status,
                "Email confirmation is still enabled in Supabase Auth",
            ) from error
        if status in {400, 401, 403}:
            raise SupabaseAuthenticationError(status, "Email or password is incorrect") from error
        raise _translate_error(error) from error


@_manage_clients
def restore_session(access_token: str, refresh_token: str) -> SupabaseSession:
    client = _client()
    try:
        response = client.auth.set_session(access_token, refresh_token)
        session = _session_from_response(response)
        if session is not None:
            return session
        user_response = client.auth.get_user(access_token)
        auth_user = _field(user_response, "user")
        if auth_user is None:
            raise SupabaseAuthenticationError(401, "Supabase session is no longer valid")
        return SupabaseSession(
            access_token=access_token,
            refresh_token=refresh_token,
            user=_application_user(client, auth_user),
        )
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def get_profile(access_token: str, refresh_token: str = "") -> dict[str, Any]:
    client = _authenticated_client(access_token)
    try:
        auth_response = client.auth.get_user(access_token)
        auth_user = _field(auth_response, "user")
        if auth_user is None:
            raise SupabaseAuthenticationError(401, "Supabase session is no longer valid")
        profile = _profile_row(client, str(_field(auth_user, "id", "")))
        return {
            **profile,
            "nome_completo": profile.get("full_name") or "",
            "foto_perfil_path": profile.get("foto_perfil") or "",
            "foto_perfil": signed_profile_photo_url(
                access_token,
                profile.get("foto_perfil") or "",
                refresh_token,
            ),
        }
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def save_profile(
    access_token: str,
    payload: dict[str, Any],
    refresh_token: str = "",
) -> dict[str, Any]:
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        if auth_user is None:
            raise SupabaseAuthenticationError(401, "Supabase session is no longer valid")
        if refresh_token:
            client.auth.set_session(access_token, refresh_token)
        user_id = str(_field(auth_user, "id", ""))
        profile_payload = {
            "full_name": str(payload.get("nome_completo") or "").strip(),
            "cpf": str(payload.get("cpf") or ""),
            "telefone": str(payload.get("telefone") or ""),
            "foto_perfil": str(payload.get("foto_perfil") or ""),
        }
        rows = (
            client.table("profiles")
            .update(profile_payload)
            .eq("id", user_id)
            .execute()
            .data
        )
        if not isinstance(rows, list) or not rows:
            raise SupabaseBackendError(500, "Supabase did not update the profile")
        return {
            **rows[0],
            "nome_completo": rows[0].get("full_name") or "",
            "foto_perfil_path": rows[0].get("foto_perfil") or "",
            "foto_perfil": signed_profile_photo_url(
                access_token,
                rows[0].get("foto_perfil") or "",
                refresh_token,
            ),
        }
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def upload_profile_photo(
    access_token: str,
    refresh_token: str,
    profile_file: dict[str, Any],
    user_id: str,
) -> str:
    mime_type = str(profile_file.get("mime_type") or "")
    if mime_type not in {"image/jpeg", "image/png"}:
        raise ValueError("Only JPEG and PNG profile photos are supported")
    content = profile_file.get("content")
    if not isinstance(content, bytes) or not content or len(content) > 5 * 1024 * 1024:
        raise ValueError("Profile photo must be between 1 byte and 5 MB")
    extension = "jpg" if mime_type == "image/jpeg" else "png"
    object_path = f"profiles/{user_id}/avatar.{extension}"
    client = _authenticated_client(access_token)
    try:
        client.auth.set_session(access_token, refresh_token)
        client.storage.from_("profile-photos").upload(
            object_path,
            content,
            {"content-type": mime_type, "upsert": "true"},
        )
        return object_path
    except Exception as error:
        if isinstance(error, SupabaseBackendError):
            raise
        raise _translate_error(error) from error


@_manage_clients
def signed_profile_photo_url(
    access_token: str,
    object_path: str,
    refresh_token: str = "",
) -> str:
    if not object_path:
        return ""
    client = _authenticated_client(access_token)
    try:
        if refresh_token:
            client.auth.set_session(access_token, refresh_token)
        result = client.storage.from_("profile-photos").create_signed_url(object_path, 3600)
        signed_url = _field(result, "signed_url") or _field(result, "signedURL")
        if not signed_url:
            raise SupabaseBackendError(502, "Supabase returned an invalid photo URL")
        return urljoin(_settings().url.rstrip("/") + "/", str(signed_url).lstrip("/"))
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def delete_profile_photo(access_token: str, refresh_token: str, object_path: str) -> None:
    if not object_path:
        return
    client = _authenticated_client(access_token)
    try:
        client.auth.set_session(access_token, refresh_token)
        client.storage.from_("profile-photos").remove([object_path])
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def fetch_user_vehicles(access_token: str) -> list[dict[str, Any]]:
    client = _authenticated_client(access_token)
    try:
        result = client.table("vehicles").select("*").order("created_at", desc=True).execute().data
        return result if isinstance(result, list) else []
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def save_vehicle(access_token: str, payload: dict[str, Any], vehicle_id: int | None = None) -> dict[str, Any]:
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        if auth_user is None:
            raise SupabaseAuthenticationError(401, "Supabase session is no longer valid")
        vehicle_fields = {
            "brand": payload["brand"],
            "model": payload["model"],
            "plate": payload["plate"],
            "year": int(payload["year"]),
            "color": payload["color"],
        }
        if vehicle_id is not None:
            query = client.table("vehicles").update(vehicle_fields).eq("id", vehicle_id)
        else:
            query = client.table("vehicles").insert(
                {
                    **vehicle_fields,
                    "user_id": str(_field(auth_user, "id", "")),
                }
            )
        result = query.execute().data
        if not isinstance(result, list) or not result:
            raise SupabaseBackendError(500, "Supabase did not save the vehicle")
        return result[0]
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def delete_vehicle(access_token: str, vehicle_id: int) -> None:
    client = _authenticated_client(access_token)
    try:
        client.table("vehicles").delete().eq("id", vehicle_id).execute()
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def fetch_pending_requests(access_token: str) -> list[dict[str, Any]]:
    client = _authenticated_client(access_token)
    try:
        result = client.rpc("list_pending_service_requests", {}).execute().data
        if not isinstance(result, list):
            raise SupabaseBackendError(
                502,
                "Supabase returned an invalid pending request list",
            )
        logger.info("Pending service request RPC returned count=%s", len(result))
        return result
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def fetch_active_service_requests(
    access_token: str,
    provider_id: str,
) -> list[dict[str, Any]]:
    if not provider_id.strip():
        raise ValueError("Provider ID is required")
    client = _authenticated_client(access_token)
    try:
        result = (
            client.table("service_requests")
            .select("*")
            .eq("provider_id", provider_id)
            .in_("status", ["accepted", "in_progress"])
            .execute()
            .data
        )
        if not isinstance(result, list):
            raise SupabaseBackendError(
                502,
                "Supabase returned an invalid active request list",
            )
        logger.info("Active service request query returned count=%s", len(result))
        return result
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def fetch_service_request(access_token: str, request_id: int) -> dict[str, Any] | None:
    client = _authenticated_client(access_token)
    try:
        rows = (
            client.table("service_requests")
            .select("*")
            .eq("id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if not isinstance(rows, list) or not rows:
            return None
        return rows[0] if isinstance(rows[0], dict) else None
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def create_service_request(
    access_token: str,
    service_type: str,
    vehicle_id: int,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    client = _authenticated_client(access_token)
    try:
        result = client.rpc(
            "create_service_request",
            {
                "p_service_type": service_type,
                "p_vehicle_id": vehicle_id,
                "p_latitude": latitude,
                "p_longitude": longitude,
            },
        ).execute().data
        row = result[0] if isinstance(result, list) and result else result
        if not isinstance(row, dict):
            raise SupabaseBackendError(502, "Supabase returned an invalid service request")
        if (
            row.get("id") is None
            or row.get("status") != "pending"
            or row.get("provider_id") is not None
        ):
            logger.error(
                "Created service request has invalid availability status=%s provider_assigned=%s has_id=%s",
                row.get("status"),
                row.get("provider_id") is not None,
                row.get("id") is not None,
            )
            raise SupabaseBackendError(
                502,
                "Supabase did not create an available pending request",
            )
        logger.info(
            "Created service request status=%s service_type=%s provider_assigned=%s",
            row["status"],
            row.get("service_type"),
            row.get("provider_id") is not None,
        )
        return {**row, "request_id": row.get("id")}
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def _request_transition(access_token: str, rpc_name: str, request_id: int) -> dict[str, Any]:
    client = _authenticated_client(access_token)
    try:
        result = client.rpc(rpc_name, {"p_request_id": int(request_id)}).execute().data
        row = result[0] if isinstance(result, list) and result else result
        if not isinstance(row, dict):
            raise SupabaseBackendError(502, "Supabase returned an invalid request status")
        return row
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


def accept_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    return _request_transition(access_token, "accept_service_request", request_id)


def release_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    return _request_transition(access_token, "release_service_request", request_id)


def complete_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    return _request_transition(access_token, "complete_service_request", request_id)


def cancel_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    return _request_transition(access_token, "cancel_service_request", request_id)


@_manage_clients
def fetch_service_messages(access_token: str, request_id: int) -> list[dict[str, Any]]:
    client = _authenticated_client(access_token)
    try:
        result = (
            client.table("service_messages")
            .select("*")
            .eq("service_request_id", int(request_id))
            .order("created_at")
            .execute()
            .data
        )
        return result if isinstance(result, list) else []
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def send_service_message(access_token: str, request_id: int, message_text: str) -> dict[str, Any]:
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        if auth_user is None:
            raise SupabaseAuthenticationError(401, "Supabase session is no longer valid")
        result = (
            client.table("service_messages")
            .insert(
                {
                    "service_request_id": int(request_id),
                    "sender_id": str(_field(auth_user, "id", "")),
                    "message_text": message_text.strip(),
                }
            )
            .execute()
            .data
        )
        if not isinstance(result, list) or not result:
            raise SupabaseBackendError(502, "Supabase did not save the message")
        return result[0]
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error
