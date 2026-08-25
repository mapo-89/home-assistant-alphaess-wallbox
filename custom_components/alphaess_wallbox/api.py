"""Token-safe client for the current AlphaESS European platform API."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from typing import Any

from aiohttp import ClientError, ClientSession

BASE_URL = "https://platform-eur.alphaess.com/api"
LOGIN_URL = f"{BASE_URL}/users-center/sessions"


class AlphaESSWallboxError(Exception):
    """Base integration error."""


class AlphaESSWallboxAuthError(AlphaESSWallboxError):
    """Authentication failed."""


class AlphaESSWallboxConnectionError(AlphaESSWallboxError):
    """The AlphaESS platform could not be reached."""


class AlphaESSWallboxApi:
    """Client which keeps OAuth tokens in memory only."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        system_sn: str,
        charger_sn: str | None = None,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self.system_sn = system_sn
        self.charger_sn = charger_sn.strip() if charger_sn else None
        self._access_token: str | None = None
        self._token_type = "Bearer"

    async def async_login(self) -> None:
        """Create a platform session without exposing tokens to HA."""
        payload = {
            "email": self._username,
            "type": "password",
            "password": self._password,
        }
        response = await self._request_json(
            "POST", LOGIN_URL, json=payload, authenticate=False
        )
        token = response.get("accessToken")
        token_type = response.get("tokenType", "Bearer")
        if not isinstance(token, str) or not token:
            raise AlphaESSWallboxAuthError("Login response contains no access token")
        self._access_token = token
        self._token_type = str(token_type or "Bearer")

    async def async_get_ess(self) -> dict[str, Any]:
        """Fetch the current ESS configuration."""
        return await self._authenticated_request(
            "GET", f"{BASE_URL}/internal/v1/ess/{self.system_sn}"
        )

    def get_charger(self, ess: dict[str, Any]) -> dict[str, Any]:
        """Resolve the configured charger without mutating the response."""
        chargers = ess.get("evCharger")
        if not isinstance(chargers, list) or not chargers:
            raise AlphaESSWallboxError("ESS response contains no EV charger")
        if self.charger_sn:
            for charger in chargers:
                if isinstance(charger, dict) and charger.get("sn") == self.charger_sn:
                    return charger
            raise AlphaESSWallboxError("Configured EV charger was not found")
        if len(chargers) != 1 or not isinstance(chargers[0], dict):
            raise AlphaESSWallboxError(
                "Multiple EV chargers found; configure a charger serial number"
            )
        return chargers[0]

    async def async_set_charging_mode(self, charging_mode: int) -> dict[str, Any]:
        """Patch the current charger block while preserving every other setting."""
        ess = await self.async_get_ess()
        chargers = ess.get("evCharger")
        if not isinstance(chargers, list):
            raise AlphaESSWallboxError("ESS response contains no EV charger list")
        patched_chargers = deepcopy(chargers)

        target: dict[str, Any] | None = None
        if self.charger_sn:
            target = next(
                (
                    charger
                    for charger in patched_chargers
                    if isinstance(charger, dict) and charger.get("sn") == self.charger_sn
                ),
                None,
            )
        elif len(patched_chargers) == 1 and isinstance(patched_chargers[0], dict):
            target = patched_chargers[0]
        if target is None:
            raise AlphaESSWallboxError("Configured EV charger was not found")

        g1t = target.get("g1T")
        if not isinstance(g1t, dict):
            raise AlphaESSWallboxError("EV charger response contains no g1T settings")
        g1t["chargeMode"] = charging_mode

        return await self._authenticated_request(
            "PATCH",
            f"{BASE_URL}/internal/v1/ess/{self.system_sn}",
            json={"evCharger": patched_chargers},
        )

    async def async_validate(self) -> None:
        """Validate credentials, system and charger during the config flow."""
        await self.async_login()
        ess = await self.async_get_ess()
        self.get_charger(ess)

    async def _authenticated_request(
        self, method: str, url: str, **kwargs: Any
    ) -> dict[str, Any]:
        if self._access_token is None:
            await self.async_login()
        try:
            return await self._request_json(method, url, **kwargs)
        except AlphaESSWallboxAuthError:
            self._access_token = None
            await self.async_login()
            return await self._request_json(method, url, **kwargs)

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Accept", "application/json")
        if authenticate:
            if self._access_token is None:
                raise AlphaESSWallboxAuthError("No access token available")
            headers["Authorization"] = f"{self._token_type} {self._access_token}"

        try:
            async with asyncio.timeout(20):
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    if response.status in (401, 403):
                        raise AlphaESSWallboxAuthError("AlphaESS session expired")
                    response.raise_for_status()
                    body = await response.text()
        except AlphaESSWallboxAuthError:
            raise
        except (TimeoutError, ClientError) as err:
            # Never include URL query data, headers, payloads, credentials or tokens.
            raise AlphaESSWallboxConnectionError(
                f"AlphaESS platform request failed ({type(err).__name__})"
            ) from err

        if not body.strip():
            return {}
        try:
            value = json.loads(body)
        except ValueError as err:
            raise AlphaESSWallboxConnectionError(
                "AlphaESS platform returned an invalid JSON response"
            ) from err
        if isinstance(value, dict):
            return value
        # PATCH responses may be an empty/list acknowledgement depending on the
        # platform release. The subsequent GET is the authoritative verification.
        return {"result": value}
