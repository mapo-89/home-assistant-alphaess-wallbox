"""Small, token-safe client for AlphaESS private wallbox endpoints."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

LOGIN_URL = "https://cloud.alphaess.com/api/stable/user/login"
WALLBOX_BASE_URL = "https://eurcloud.alphaess.com/api/iterate"

AUTH_ERROR_CODES = {401, 403, 6070}
AUTH_ERROR_MESSAGES = {
    "illegal login",
    "the sign-in status has expired",
    "the token cannot be empty",
}


class AlphaESSWallboxError(Exception):
    """Base integration error."""


class AlphaESSWallboxAuthError(AlphaESSWallboxError):
    """Authentication failed."""


class AlphaESSWallboxConnectionError(AlphaESSWallboxError):
    """The AlphaESS cloud could not be reached."""


class AlphaESSWallboxApi:
    """Client which keeps access and refresh tokens in memory only."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        system_sn: str,
        charging_pile_id: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self.system_sn = system_sn
        self.charging_pile_id = charging_pile_id
        self._token: str | None = None

    async def async_login(self) -> None:
        """Authenticate without exposing credentials or tokens to HA states/logs."""
        payload = {"username": self._username, "password": self._password}
        response = await self._request_json("POST", LOGIN_URL, json=payload, authenticate=False)

        code = _as_int(response.get("code"))
        data = response.get("data")
        token = data.get("token") if isinstance(data, dict) else None
        if code != 200 or not isinstance(token, str) or not token:
            raise AlphaESSWallboxAuthError(_safe_error(response, "Login failed"))
        self._token = token

    async def async_get_wallbox_config(self) -> dict[str, Any]:
        """Return the wallbox configuration."""
        return await self._authenticated_request(
            "GET",
            f"{WALLBOX_BASE_URL}/newEv/getNewEvBySn",
            params={"sysSn": self.system_sn},
        )

    async def async_get_wallbox_status(self) -> dict[str, Any]:
        """Return the wallbox status."""
        return await self._authenticated_request(
            "GET",
            f"{WALLBOX_BASE_URL}/ev/v2/getChargPileStatusByPileSn",
            params={"sysSn": self.system_sn, "chargingpileId": self.charging_pile_id},
        )

    async def async_set_charging_mode(self, charging_mode: int) -> dict[str, Any]:
        """Set the private-cloud charging mode using the proven curl payload."""
        payload = {
            "sysSn": self.system_sn,
            "isNewPile": False,
            "chargingpileControlOpen": True,
            "oldPileData": {
                "chargingmode": charging_mode,
                "chargingpileSwitch": True,
                "timeCharge1": False,
                "timeCharge2": False,
            },
        }
        return await self._authenticated_request(
            "POST", f"{WALLBOX_BASE_URL}/newEv/setNewEv", json=payload
        )

    async def async_validate(self) -> None:
        """Validate credentials and system serial during the config flow."""
        await self.async_login()
        await self.async_get_wallbox_config()

    async def _authenticated_request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        if self._token is None:
            await self.async_login()

        response = await self._request_json(method, url, **kwargs)
        if _is_auth_error(response):
            self._token = None
            await self.async_login()
            response = await self._request_json(method, url, **kwargs)

        if _is_auth_error(response):
            raise AlphaESSWallboxAuthError(_safe_error(response, "Authentication expired"))
        if _as_int(response.get("code")) != 200:
            raise AlphaESSWallboxError(_safe_error(response, "AlphaESS request failed"))
        return response

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}))
        if authenticate:
            if self._token is None:
                raise AlphaESSWallboxAuthError("No access token available")
            headers["Authorization"] = self._token

        try:
            async with asyncio.timeout(20):
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    response.raise_for_status()
                    value = await response.json(content_type=None)
        except (TimeoutError, ClientError, ClientResponseError) as err:
            # Never include request headers, payloads, credentials, or tokens here.
            raise AlphaESSWallboxConnectionError(
                f"AlphaESS cloud request failed ({type(err).__name__})"
            ) from err
        except ValueError as err:
            raise AlphaESSWallboxConnectionError(
                "AlphaESS cloud returned an invalid JSON response"
            ) from err

        if not isinstance(value, dict):
            raise AlphaESSWallboxConnectionError("AlphaESS cloud returned an unexpected response")
        return value


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_auth_error(response: dict[str, Any]) -> bool:
    code = _as_int(response.get("code"))
    message = str(response.get("msg", "")).strip().lower()
    return code in AUTH_ERROR_CODES or message in AUTH_ERROR_MESSAGES


def _safe_error(response: dict[str, Any], fallback: str) -> str:
    code = _as_int(response.get("code"))
    message = str(response.get("msg", "")).strip()
    if message:
        return f"{message} (code {code})" if code is not None else message
    return f"{fallback} (code {code})" if code is not None else fallback
