"""
Shared HTTP behaviour for OpenAlex (retries, backoff, error shaping).

Environment (optional):
  OPENALEX_MAX_RETRIES — default 3 (429/503/502 only)
  OPENALEX_RETRY_BACKOFF_SEC — base seconds for exponential backoff, default 0.75
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return max(0.05, float(raw))
    except ValueError:
        return default


def openalex_http_detail(exc: BaseException) -> str:
    """Human-readable message for API / client errors (logs + HTTPException detail)."""
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        try:
            body = exc.response.text
            snippet = (body[:400] + "…") if len(body) > 400 else body
        except Exception:  # noqa: BLE001
            snippet = ""
        if code == 429:
            return "OpenAlex rate-limited this request (HTTP 429). Wait briefly, set OPENALEX_MAILTO in .env, or reduce batch size."
        if code in (502, 503, 504):
            return f"OpenAlex returned HTTP {code} (temporary). Retry in a few seconds."
        if code == 400:
            return f"OpenAlex rejected the request (HTTP 400). Check filters/sort parameters. Response: {snippet or 'empty body'}"
        if code == 404:
            return "OpenAlex returned HTTP 404 (not found)."
        return f"OpenAlex HTTP {code}: {snippet or exc.response.reason_phrase}"
    if isinstance(exc, httpx.TimeoutException):
        return "OpenAlex request timed out. Try again or increase timeout."
    if isinstance(exc, httpx.RequestError):
        return f"Network error calling OpenAlex: {exc!s}"
    return f"OpenAlex error: {exc!s}"


async def openalex_get_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any],
    *,
    max_retries: int | None = None,
    allow_not_found: bool = False,
) -> dict[str, Any] | None:
    """
    GET *url* with *params*; retry on 429 / 502 / 503 with exponential backoff.
    Raises httpx.HTTPStatusError on final non-retryable failure.
    """
    retries = max_retries if max_retries is not None else _env_int("OPENALEX_MAX_RETRIES", 3)
    base = _env_float("OPENALEX_RETRY_BACKOFF_SEC", 0.75)
    for attempt in range(retries + 1):
        try:
            r = await client.get(url, params=params)
            if r.status_code == 404 and allow_not_found:
                return None
            if r.status_code in (429, 502, 503) and attempt < retries:
                wait = base * (2**attempt)
                logger.warning(
                    "OpenAlex GET %s returned %s; retry %s/%s in %.1fs",
                    url,
                    r.status_code,
                    attempt + 1,
                    retries,
                    wait,
                )
                await asyncio.sleep(wait)
                continue
            r.raise_for_status()
            out = r.json()
            return out if isinstance(out, dict) else {}
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404 and allow_not_found:
                return None
            if exc.response.status_code in (429, 502, 503) and attempt < retries:
                wait = base * (2**attempt)
                logger.warning(
                    "OpenAlex HTTPStatusError %s; retry %s/%s in %.1fs",
                    exc.response.status_code,
                    attempt + 1,
                    retries,
                    wait,
                )
                await asyncio.sleep(wait)
                continue
            raise
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt < retries:
                wait = base * (2**attempt)
                logger.warning("OpenAlex transport error; retry %s/%s in %.1fs", attempt + 1, retries, wait)
                await asyncio.sleep(wait)
                continue
            raise
    raise RuntimeError("openalex_get_json: unreachable")
