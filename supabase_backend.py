"""User-scoped Supabase operations for the Reflex application."""

from __future__ import annotations

import logging
import math
import os
import hmac
import re

from contextvars import ContextVar
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import httpx
import requests
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


def _service_client() -> Client:
    current = _settings()
    if not current.service_role_key:
        raise SupabaseConfigurationRuntimeError(
            503,
            "Supabase service role key is required for payment operations",
        )
    try:
        client = create_client(
            current.url,
            current.service_role_key,
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
        if status == 422:
            raise SupabaseBackendError(
                422,
                "Supabase rejected weak password or invalid signup data",
            ) from error
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
def request_password_reset(email: str, redirect_origin: str) -> None:
    """Request a Supabase password recovery email."""
    client = _client()
    redirect_origin = redirect_origin.strip().rstrip("/")
    email = email.strip().lower()
    if not email or "@" not in email:
        raise SupabaseAuthenticationError(400, "Invalid email")
    parsed_redirect = urlsplit(redirect_origin)
    if (
        parsed_redirect.scheme not in {"http", "https"}
        or not parsed_redirect.hostname
        or parsed_redirect.username
        or parsed_redirect.password
        or parsed_redirect.query
        or parsed_redirect.fragment
    ):
        raise SupabaseBackendError(400, "Invalid recovery redirect origin")
    try:
        client.auth.reset_password_for_email(
            email.strip().lower(),
            {"redirect_to": f"{redirect_origin}/redefinir-senha"},
        )
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def update_password(access_token: str, refresh_token: str, password: str) -> None:
    """Update the password for the recovery session."""
    password = password or ""
    if len(password) < 6:
        raise SupabaseAuthenticationError(400, "Password must contain at least 6 characters")
    client = _client()
    try:
        client.auth.set_session(access_token.strip(), refresh_token.strip())
        client.auth.update_user({"password": password})
    except SupabaseBackendError:
        raise
    except Exception as error:
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


def start_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    request = _request_transition(access_token, "start_service_request", request_id)
    if request.get("status") != "in_progress":
        logger.error(
            "Started service request returned unexpected status=%s",
            request.get("status"),
        )
        raise SupabaseBackendError(502, "Supabase did not start the service request")
    return request


def complete_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    return _request_transition(access_token, "complete_service_request", request_id)


def cancel_service_request(access_token: str, request_id: int) -> dict[str, Any]:
    return _request_transition(access_token, "cancel_service_request", request_id)


def _asaas_settings() -> tuple[str, str]:
    api_key = os.getenv("ASAAS_API_KEY", "").strip()
    api_url = os.getenv(
        "ASAAS_API_URL",
        "https://api-sandbox.asaas.com/v3",
    ).strip().rstrip("/")
    if not api_key:
        raise SupabaseConfigurationRuntimeError(503, "Asaas API key is not configured")
    if not api_url.startswith("https://"):
        raise SupabaseConfigurationRuntimeError(503, "Asaas API URL is invalid")
    return api_key, api_url


def _asaas_error_codes(response: requests.Response) -> list[str]:
    try:
        body = response.json()
    except ValueError:
        return []
    if not isinstance(body, dict) or not isinstance(body.get("errors"), list):
        return []
    codes = {
        item["code"].strip()
        for item in body["errors"]
        if isinstance(item, dict)
        and isinstance(item.get("code"), str)
        and 0 < len(item["code"].strip()) <= 80
        and all(character.isalnum() or character in "._-" for character in item["code"].strip())
    }
    return sorted(codes)


def _asaas_error_details(response: requests.Response) -> list[str]:
    try:
        body = response.json()
    except ValueError:
        return []
    if not isinstance(body, dict) or not isinstance(body.get("errors"), list):
        return []

    details = set()
    for item in body["errors"]:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        description = item.get("description")
        if not isinstance(code, str) or not isinstance(description, str):
            continue
        safe_code = code.strip()
        if (
            not safe_code
            or len(safe_code) > 80
            or not all(char.isalnum() or char in "._-" for char in safe_code)
        ):
            continue
        safe_description = re.sub(r"https?://\S+", "[URL]", description)
        safe_description = re.sub(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            "[email]",
            safe_description,
            flags=re.IGNORECASE,
        )
        safe_description = re.sub(r"\b\d{8,}\b", "[number]", safe_description)
        safe_description = re.sub(
            r"\b[A-Za-z0-9_-]{32,}\b",
            "[redacted]",
            safe_description,
        )
        safe_description = "".join(
            character
            for character in safe_description
            if character.isprintable()
        )
        safe_description = " ".join(safe_description.split())[:240]
        if safe_description:
            details.add(f"{safe_code}: {safe_description}")
    return sorted(details)


@_manage_clients
def create_service_payment(
    access_token: str,
    request_id: int,
    payment_method: str,
) -> dict[str, Any]:
    """Create an authorized, hosted Asaas checkout for a completed request."""
    if payment_method != "credit_card":
        raise SupabaseBackendError(400, "Only credit card payments are supported")

    client = _authenticated_client(access_token)
    try:
        rows = client.table("service_requests").select(
            "id,user_id,provider_id,estimated_price,status"
        ).eq("id", int(request_id)).limit(1).execute().data
        if not isinstance(rows, list) or not rows:
            raise SupabaseAuthenticationError(404, "Service request not found")
        request = rows[0]
        auth_identity = _field(client.auth.get_user(access_token), "user")
        customer_id = str(_field(auth_identity, "id", "") or "")
        if str(request.get("user_id") or "") != customer_id:
            raise SupabaseAuthenticationError(403, "Payment is not owned by this customer")
        if request.get("status") != "completed":
            raise SupabaseBackendError(409, "Service request is not completed")

        amount = float(request.get("estimated_price") or 0)
        if not math.isfinite(amount) or amount <= 0:
            raise SupabaseBackendError(422, "Service request has no valid payment amount")

        api_key, api_url = _asaas_settings()
        service_client = _service_client()
        existing_rows = (
            service_client.table("service_request_payments")
            .select("payment_method,status,gateway_checkout_id,checkout_url,amount")
            .eq("service_request_id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if isinstance(existing_rows, list) and existing_rows:
            existing = existing_rows[0]
            if existing.get("status") == "confirmed":
                raise SupabaseBackendError(409, "Service request payment is already confirmed")
            if (
                existing.get("status") == "pending"
                and existing.get("checkout_url")
                and existing.get("payment_method") == payment_method
            ):
                return {
                    "payment_method": payment_method,
                    "status": "pending",
                    "amount": amount,
                    "gateway_checkout_id": existing.get("gateway_checkout_id"),
                    "checkout_url": existing["checkout_url"],
                }
            if existing.get("status") == "pending" and existing.get("checkout_url"):
                raise SupabaseBackendError(409, "Another payment checkout is already pending")

        return_base_url = os.getenv("ASAAS_CHECKOUT_RETURN_URL", "").strip().rstrip("/")
        try:
            parsed_return_url = urlsplit(return_base_url)
            valid_return_url = (
                parsed_return_url.scheme == "https"
                and bool(parsed_return_url.hostname)
                and parsed_return_url.username is None
                and parsed_return_url.password is None
                and parsed_return_url.hostname.lower() != "localhost"
                and parsed_return_url.path in {"", "/"}
                and not parsed_return_url.query
                and not parsed_return_url.fragment
            )
        except ValueError:
            valid_return_url = False
        if not valid_return_url:
            raise SupabaseConfigurationRuntimeError(
                503,
                "Asaas checkout callback URL must be a public HTTPS origin",
            )

        callback_base_url = f"{return_base_url}/api/asaas/checkout-return"
        checkout_payload: dict[str, Any] = {
            "billingTypes": ["CREDIT_CARD"],
            "chargeTypes": ["DETACHED"],
            "minutesToExpire": 1440,
            "externalReference": f"service-request:{int(request_id)}",
            "callback": {
                "successUrl": f"{callback_base_url}/success",
                "cancelUrl": f"{callback_base_url}/cancel",
                "expiredUrl": f"{callback_base_url}/expired",
            },
            "items": [
                {
                    "name": "Atendimento SOS Drive",
                    "description": f"Chamado #{int(request_id)}",
                    "imageBase64": (
                        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNgAAIAAAUAAXpeqz8AAAAASUVORK5CYII="
                    ),
                    "quantity": 1,
                    "value": amount,
                }
            ],
        }
        response = requests.post(
            f"{api_url}/checkouts",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "access_token": api_key,
            },
            json=checkout_payload,
            timeout=15,
        )
        if response.status_code >= 400:
            error_codes = _asaas_error_codes(response)
            error_details = _asaas_error_details(response)
            logger.error(
                "Asaas payment creation failed status=%s error_codes=%s",
                response.status_code,
                error_codes,
            )
            raise SupabaseBackendError(
                response.status_code,
                "Asaas rejected the payment; "
                f"error_codes={','.join(error_codes)}; "
                f"error_details={' | '.join(error_details)}",
            )
        payload = response.json()
        checkout_id = str(payload.get("id") or "")
        checkout_url = str(payload.get("link") or "")
        if not checkout_id or not checkout_url:
            raise SupabaseBackendError(502, "Asaas did not return a checkout link")
        try:
            service_client.table("service_request_payments").upsert(
                {
                    "service_request_id": int(request_id),
                    "customer_id": customer_id,
                    "provider_id": request.get("provider_id"),
                    "gateway": "asaas",
                    "gateway_checkout_id": checkout_id,
                    "checkout_url": checkout_url,
                    "payment_method": payment_method,
                    "amount": amount,
                    "status": "pending",
                    "gateway_payload": payload,
                },
                on_conflict="service_request_id",
            ).execute()
        except Exception:
            logger.error("Payment record persistence failed for service request=%s", int(request_id))
            raise SupabaseBackendError(
                502,
                "Payment was created but could not be persisted",
            ) from None
        return {
            "payment_method": payment_method,
            "status": "pending",
            "amount": amount,
            "gateway_checkout_id": checkout_id,
            "checkout_url": checkout_url,
        }
    except (SupabaseBackendError, SupabaseAuthenticationError):
        raise
    except (requests.RequestException, TypeError, ValueError):
        raise SupabaseBackendError(503, "Asaas payment service unavailable") from None


@_manage_clients
def fetch_service_payment_context(
    access_token: str,
    request_id: int | None = None,
) -> dict[str, Any]:
    """Load the customer's completed request and display-safe payment summary."""
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        customer_id = str(_field(auth_user, "id", "") or "")
        query = (
            client.table("service_requests")
            .select(
                "id,user_id,provider_id,vehicle_id,service_type,estimated_price,distance_km,status,created_at"
            )
            .eq("user_id", customer_id)
            .eq("status", "completed")
        )
        if request_id is not None:
            query = query.eq("id", int(request_id))
        rows = query.order("created_at", desc=True).limit(1).execute().data
        if not isinstance(rows, list) or not rows:
            raise SupabaseBackendError(404, "No completed service request is available")
        request = rows[0]
        service_client = _service_client()
        provider_name = ""
        vehicle_description = ""
        if request.get("provider_id"):
            provider_rows = (
                service_client.table("profiles")
                .select("full_name")
                .eq("id", request["provider_id"])
                .limit(1)
                .execute()
                .data
            )
            if isinstance(provider_rows, list) and provider_rows:
                provider_name = str(provider_rows[0].get("full_name") or "")
        vehicle_rows = (
            service_client.table("vehicles")
            .select("brand,model,year")
            .eq("id", request["vehicle_id"])
            .limit(1)
            .execute()
            .data
        )
        if isinstance(vehicle_rows, list) and vehicle_rows:
            vehicle = vehicle_rows[0]
            vehicle_description = " ".join(
                str(vehicle.get(field) or "")
                for field in ("brand", "model", "year")
                if vehicle.get(field)
            )
        return {
            "request_id": int(request["id"]),
            "service_type": str(request.get("service_type") or ""),
            "estimated_price": float(request.get("estimated_price") or 0),
            "distance_km": float(request.get("distance_km") or 0),
            "created_at": str(request.get("created_at") or ""),
            "provider_name": provider_name,
            "vehicle_description": vehicle_description,
        }
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


def _reconcile_pending_asaas_payment(
    service_client: Client,
    payment: dict[str, Any],
) -> dict[str, Any]:
    checkout_id = str(payment.get("gateway_checkout_id") or "")
    if (
        payment.get("status") != "pending"
        or payment.get("payment_method") != "credit_card"
        or not checkout_id
    ):
        return payment

    api_key, api_url = _asaas_settings()
    try:
        response = requests.get(
            f"{api_url}/payments",
            headers={
                "accept": "application/json",
                "access_token": api_key,
            },
            params={"checkoutSession": checkout_id, "limit": 10},
            timeout=15,
        )
    except requests.RequestException as error:
        logger.error(
            "Asaas payment reconciliation request failed category=%s",
            type(error).__name__,
        )
        raise SupabaseBackendError(503, "Asaas payment status is unavailable") from None

    if response.status_code >= 400:
        logger.error(
            "Asaas payment reconciliation failed status=%s error_codes=%s",
            response.status_code,
            _asaas_error_codes(response),
        )
        raise SupabaseBackendError(503, "Asaas payment status is unavailable")

    try:
        payload = response.json()
    except ValueError:
        logger.error("Asaas payment reconciliation returned invalid JSON")
        raise SupabaseBackendError(502, "Asaas payment status is invalid") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        logger.error("Asaas payment reconciliation returned an invalid response")
        raise SupabaseBackendError(502, "Asaas payment status is invalid")

    matching_payments = [
        item
        for item in payload["data"]
        if isinstance(item, dict)
        and str(item.get("checkoutSession") or "") == checkout_id
    ]
    if len(matching_payments) != 1:
        if len(matching_payments) > 1:
            logger.warning("Asaas payment reconciliation returned ambiguous results")
        return payment

    asaas_payment = matching_payments[0]
    try:
        persisted_amount = Decimal(str(payment.get("amount")))
        asaas_amount = Decimal(str(asaas_payment.get("value")))
        cent = Decimal("0.01")
        amount_matches = (
            persisted_amount.is_finite()
            and asaas_amount.is_finite()
            and persisted_amount == persisted_amount.quantize(cent)
            and asaas_amount == asaas_amount.quantize(cent)
            and persisted_amount == asaas_amount
        )
    except (InvalidOperation, TypeError, ValueError):
        amount_matches = False

    if not amount_matches:
        logger.warning("Asaas payment reconciliation amount did not match")
        return payment
    if str(asaas_payment.get("status") or "").upper() not in {
        "CONFIRMED",
        "RECEIVED",
    }:
        return payment

    asaas_payment_id = str(asaas_payment.get("id") or "")
    if not asaas_payment_id:
        logger.warning("Asaas confirmed payment response has no payment identifier")
        return payment

    (
        service_client.table("service_request_payments")
        .update(
            {
                "status": "confirmed",
                "gateway_payment_id": asaas_payment_id,
            }
        )
        .eq("id", payment["id"])
        .eq("status", "pending")
        .execute()
    )
    current_rows = (
        service_client.table("service_request_payments")
        .select("status")
        .eq("id", payment["id"])
        .limit(1)
        .execute()
        .data
    )
    if isinstance(current_rows, list) and current_rows:
        payment["status"] = str(current_rows[0].get("status") or payment["status"])
    return payment


@_manage_clients
def fetch_service_payment_status(
    access_token: str,
    request_id: int,
    reconcile_with_gateway: bool = False,
) -> dict[str, Any] | None:
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        participant_id = str(_field(auth_user, "id", "") or "")
        request_rows = (
            client.table("service_requests")
            .select("id,user_id,provider_id,status")
            .eq("id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if not isinstance(request_rows, list) or not request_rows:
            return None
        request = request_rows[0]
        if participant_id not in {
            str(request.get("user_id") or ""),
            str(request.get("provider_id") or ""),
        }:
            raise SupabaseAuthenticationError(403, "Payment is not accessible")
        service_client = _service_client()
        payment_rows = (
            service_client.table("service_request_payments")
            .select(
                "id,customer_id,status,payment_method,amount,updated_at,checkout_url,gateway_checkout_id"
            )
            .eq("service_request_id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if not isinstance(payment_rows, list) or not payment_rows:
            return {"status": "not_created", "payment_method": "", "amount": 0}
        result = dict(payment_rows[0])
        if reconcile_with_gateway:
            result = _reconcile_pending_asaas_payment(service_client, result)
        if participant_id != str(result.get("customer_id") or ""):
            result.pop("checkout_url", None)
        result.pop("id", None)
        result.pop("gateway_checkout_id", None)
        return result
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def process_asaas_webhook(payload: dict[str, Any], received_token: str) -> dict[str, Any]:
    """Validate and apply an Asaas payment webhook idempotently."""
    expected_token = os.getenv("ASAAS_WEBHOOK_TOKEN", "").strip()
    if not expected_token:
        raise SupabaseBackendError(503, "Asaas webhook token is not configured")
    if not received_token or not hmac.compare_digest(
        received_token.strip(),
        expected_token,
    ):
        raise SupabaseAuthenticationError(401, "Invalid Asaas webhook token")

    event = str(payload.get("event") or "")
    checkout = payload.get("checkout") if isinstance(payload.get("checkout"), dict) else {}
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    checkout_id = str(checkout.get("id") or "")
    gateway_payment_id = str(payment.get("id") or "")
    external_reference = str(payment.get("externalReference") or "")
    status_by_event = {
        "CHECKOUT_PAID": "confirmed",
        "PAYMENT_RECEIVED": "confirmed",
        "PAYMENT_CONFIRMED": "confirmed",
        "CHECKOUT_CANCELED": "cancelled",
        "PAYMENT_DELETED": "cancelled",
        "CHECKOUT_EXPIRED": "expired",
        "PAYMENT_OVERDUE": "expired",
        "PAYMENT_REFUNDED": "failed",
    }
    status = status_by_event.get(event)
    if status is None:
        return {"processed": False, "reason": "event_ignored"}
    if not checkout_id and not gateway_payment_id and not external_reference:
        raise SupabaseBackendError(400, "Asaas webhook has no checkout or payment reference")

    client = _service_client()
    try:
        query = client.table("service_request_payments").select(
            "id,status,gateway_checkout_id,gateway_payment_id"
        )
        if checkout_id:
            query = query.eq("gateway_checkout_id", checkout_id)
        elif gateway_payment_id:
            query = query.eq("gateway_payment_id", gateway_payment_id)
        else:
            prefix = "service-request:"
            if not external_reference.startswith(prefix):
                raise SupabaseBackendError(400, "Asaas webhook has no payment reference")
            try:
                request_id = int(external_reference[len(prefix):])
            except ValueError:
                raise SupabaseBackendError(400, "Asaas webhook payment reference is invalid") from None
            query = query.eq("service_request_id", request_id)
        rows = query.limit(1).execute().data
        if (
            (not isinstance(rows, list) or not rows)
            and external_reference.startswith("service-request:")
        ):
            try:
                request_id = int(external_reference.removeprefix("service-request:"))
            except ValueError:
                raise SupabaseBackendError(400, "Asaas webhook payment reference is invalid") from None
            rows = (
                client.table("service_request_payments")
                .select("id,status,gateway_checkout_id,gateway_payment_id")
                .eq("service_request_id", request_id)
                .limit(1)
                .execute()
                .data
            )
        if not isinstance(rows, list) or not rows:
            return {"processed": False, "reason": "checkout_not_found"}
        record = rows[0]
        if record.get("status") == status:
            return {"processed": True, "duplicate": True}
        if record.get("status") == "confirmed":
            return {"processed": True, "duplicate": False, "reason": "already_confirmed"}
        update_data: dict[str, Any] = {
            "status": status,
            "gateway_payload": payload,
        }
        if gateway_payment_id:
            update_data["gateway_payment_id"] = gateway_payment_id
        client.table("service_request_payments").update(
            update_data
        ).eq("id", record["id"]).execute()
        return {"processed": True, "duplicate": False}
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def fetch_service_review_for_request(
    access_token: str,
    request_id: int,
) -> dict[str, Any] | None:
    """Return the authenticated participant's review for one paid request."""
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        reviewer_id = str(_field(auth_user, "id", "") or "")
        request_rows = (
            client.table("service_requests")
            .select("id,user_id,provider_id,status")
            .eq("id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if not isinstance(request_rows, list) or not request_rows:
            raise SupabaseAuthenticationError(404, "Service request not found")
        request = request_rows[0]
        if reviewer_id not in {
            str(request.get("user_id") or ""),
            str(request.get("provider_id") or ""),
        }:
            raise SupabaseAuthenticationError(403, "Reviewer is not a participant")
        if request.get("status") != "completed":
            raise SupabaseBackendError(409, "Service request is not completed")
        payment_rows = (
            _service_client().table("service_request_payments")
            .select("status")
            .eq("service_request_id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if (
            not isinstance(payment_rows, list)
            or not payment_rows
            or payment_rows[0].get("status") != "confirmed"
        ):
            raise SupabaseBackendError(409, "Payment is not confirmed")
        reviews = (
            _service_client().table("service_request_reviews")
            .select("rating,comment,created_at")
            .eq("service_request_id", int(request_id))
            .eq("reviewer_id", reviewer_id)
            .limit(1)
            .execute()
            .data
        )
        return reviews[0] if isinstance(reviews, list) and reviews else None
    except SupabaseBackendError:
        raise
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def submit_service_review(
    access_token: str,
    request_id: int,
    rating: int,
    comment: str,
) -> dict[str, Any]:
    if rating not in {1, 2, 3, 4, 5}:
        raise SupabaseBackendError(400, "Invalid rating")

    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        reviewer_id = str(_field(auth_user, "id", "") or "")
        if not reviewer_id:
            raise SupabaseAuthenticationError(401, "Authentication is required")

        request_rows = (
            client.table("service_requests")
            .select("id,user_id,provider_id,status")
            .eq("id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if not isinstance(request_rows, list) or not request_rows:
            raise SupabaseAuthenticationError(404, "Service request not found")
        request = request_rows[0]
        customer_id = str(request.get("user_id") or "")
        provider_id = str(request.get("provider_id") or "")
        if reviewer_id not in {customer_id, provider_id}:
            raise SupabaseAuthenticationError(403, "Reviewer is not a participant")
        if request.get("status") != "completed":
            raise SupabaseBackendError(409, "Service request is not completed")

        payment_rows = (
            _service_client().table("service_request_payments")
            .select("status")
            .eq("service_request_id", int(request_id))
            .limit(1)
            .execute()
            .data
        )
        if (
            not isinstance(payment_rows, list)
            or not payment_rows
            or payment_rows[0].get("status") != "confirmed"
        ):
            raise SupabaseBackendError(409, "Payment is not confirmed")

        reviewee_id = provider_id if reviewer_id == customer_id else customer_id
        result = (
            _service_client().table("service_request_reviews")
            .insert(
                {
                    "service_request_id": int(request_id),
                    "reviewer_id": reviewer_id,
                    "reviewee_id": reviewee_id,
                    "rating": rating,
                    "comment": comment.strip()[:500],
                }
            )
            .execute()
            .data
        )
        if not isinstance(result, list) or not result:
            raise SupabaseBackendError(502, "Review was not saved")
        return result[0]
    except SupabaseBackendError:
        raise
    except Exception as error:
        code = getattr(error, "code", "")
        if str(code) == "23505":
            raise SupabaseBackendError(409, "Review already submitted") from None
        raise _translate_error(error) from error


@_manage_clients
def fetch_provider_earnings_balance(access_token: str) -> dict[str, Any]:
    """Return only the authenticated provider's confirmed service earnings."""
    client = _authenticated_client(access_token)
    try:
        auth_user = _field(client.auth.get_user(access_token), "user")
        provider_id = str(_field(auth_user, "id", "") or "")
        if not provider_id:
            raise SupabaseAuthenticationError(401, "Authentication is required")
        profile = _profile_row(client, provider_id)
        if profile.get("role") != "prestador":
            raise SupabaseAuthenticationError(403, "Provider earnings are restricted")

        rows = (
            _service_client()
            .table("provider_earnings")
            .select("amount")
            .eq("provider_id", provider_id)
            .execute()
            .data
        )
        earnings = rows if isinstance(rows, list) else []
        total = Decimal("0.00")
        for earning in earnings:
            if not isinstance(earning, dict):
                raise SupabaseBackendError(502, "Supabase returned invalid earnings")
            amount = Decimal(str(earning.get("amount")))
            if not amount.is_finite() or amount < 0:
                raise SupabaseBackendError(502, "Supabase returned invalid earnings")
            total += amount
        return {
            "balance": float(total.quantize(Decimal("0.01"))),
            "count": len(earnings),
        }
    except SupabaseBackendError:
        raise
    except (InvalidOperation, TypeError, ValueError):
        raise SupabaseBackendError(502, "Supabase returned invalid earnings") from None
    except Exception as error:
        raise _translate_error(error) from error


@_manage_clients
def fetch_service_reviews(access_token: str, user_id: str) -> dict[str, Any]:
    auth_client = _authenticated_client(access_token)
    try:
        auth_user = _field(auth_client.auth.get_user(access_token), "user")
        if str(_field(auth_user, "id", "") or "") != user_id:
            raise SupabaseAuthenticationError(403, "Reviews are only available for the current profile")
        client = _service_client()
        rows = (
            client.table("service_request_reviews")
            .select("id,rating,comment,created_at,reviewer_id,reviewee_id")
            .eq("reviewee_id", user_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )
        reviews = rows if isinstance(rows, list) else []
        rating_values = [
            int(review["rating"])
            for review in reviews
            if isinstance(review, dict) and 1 <= int(review.get("rating") or 0) <= 5
        ]
        average = (
            sum(rating_values) / len(rating_values)
            if rating_values
            else 0.0
        )
        return {
            "average": round(average, 1),
            "count": len(rating_values),
            "reviews": reviews,
        }
    except Exception as error:
        raise _translate_error(error) from error


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
