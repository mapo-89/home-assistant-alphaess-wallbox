"""Coordinator for AlphaESS Wallbox."""

from __future__ import annotations

from datetime import timedelta
import asyncio
import logging
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import AlphaESSWallboxApi, AlphaESSWallboxAuthError, AlphaESSWallboxError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AlphaESSWallboxCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch safe wallbox data while keeping tokens inside the API object."""

    def __init__(self, hass, api: AlphaESSWallboxApi, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            ess = await self.api.async_get_ess()
            charger = self.api.get_charger(ess)
        except AlphaESSWallboxAuthError as err:
            raise ConfigEntryAuthFailed("AlphaESS credentials were rejected") from err
        except AlphaESSWallboxError as err:
            raise UpdateFailed(str(err)) from err
        return {"ess": ess, "charger": charger}

    async def async_set_charging_mode(self, charging_mode: int) -> dict[str, Any]:
        """Set a mode and verify that AlphaESS persisted it."""
        result = await self.api.async_set_charging_mode(charging_mode)
        for _attempt in range(5):
            await asyncio.sleep(3)
            ess = await self.api.async_get_ess()
            charger = self.api.get_charger(ess)
            g1t = charger.get("g1T")
            actual_mode = g1t.get("chargeMode") if isinstance(g1t, dict) else None
            try:
                persisted_mode = int(actual_mode)
            except (TypeError, ValueError):
                persisted_mode = None
            if persisted_mode == charging_mode:
                await self.async_refresh()
                return result
        await self.async_refresh()
        raise AlphaESSWallboxError(
            f"AlphaESS accepted the request but retained charging mode {actual_mode}"
        )
