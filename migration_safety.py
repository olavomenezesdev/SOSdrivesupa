"""Privacy safeguards for event metadata."""

from __future__ import annotations

import re
from typing import Any


_SENSITIVE_FIELD_MARKERS = re.compile(
    r"password|passwd|secret|token|credential|authorization|cookie|api.?key|"
    r"private.?key|access.?key|(^|_)hash($|_)",
    re.IGNORECASE,
)


def sanitize_event_metadata(value: Any) -> Any:
    """Recursively remove password, hash, token, and secret fields from metadata."""
    if isinstance(value, dict):
        return {
            key: sanitize_event_metadata(item)
            for key, item in value.items()
            if not _SENSITIVE_FIELD_MARKERS.search(str(key))
        }
    if isinstance(value, list):
        return [sanitize_event_metadata(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_event_metadata(item) for item in value)
    return value
