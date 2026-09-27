from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .attributes import action_generator, attribute_generator
from .sse import SSE_HEADERS, ServerSentEventGenerator

__all__ = [
    "SSE_HEADERS",
    "ServerSentEventGenerator",
    "action_generator",
    "attribute_generator",
    "datastar_url",
]


def datastar_url(version: str | None = None) -> str:
    """Return the jsDelivr URL for the Datastar JavaScript module.

    Accepts major, minor, or exact versions with an optional ``v`` prefix.
    Major, minor, and omitted versions can resolve to the latest release.
    """
    ref = ""
    if version is not None:
        if not isinstance(version, str):
            raise TypeError("version must be a string or None")
        if not re.fullmatch(
            r"v?[0-9]+(?:\.[0-9]+(?:\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?)?)?",
            version,
        ):
            raise ValueError(
                "version must be a valid jsdelivr compatible string, such as 'v1', '1.0', or '1.0.4'"
            )
        ref = f"@v{version.removeprefix('v')}"
    return f"https://cdn.jsdelivr.net/gh/starfederation/datastar{ref}/bundles/datastar.js"


def _read_signals(
    method: str, headers: Mapping[str, str], params: Mapping, body: str | bytes
) -> dict[str, Any] | None:
    if "Datastar-Request" not in headers:
        return None
    if method in ("GET", "DELETE"):
        data = params.get("datastar")
    elif headers.get("Content-Type") == "application/json":
        data = body
    else:
        return None
    return json.loads(data) if data else None
