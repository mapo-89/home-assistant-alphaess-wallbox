"""Coordinator for AlphaESS Wallbox."""

from __future__ import annotations

from datetime import timedelta
import asyncio
import logging
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import AlphaESSWallboxApi, AlphaESSWallboxAuthError, AlphaESSWallboxError, read_charging_current
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
        self._charger_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with self._charger_lock:
                ess = await self.api.async_get_ess()
                charger = self.api.get_charger(ess)
        except AlphaESSWallboxAuthError as err:
            raise ConfigEntryAuthFailed("AlphaESS credentials were rejected") from err
        except AlphaESSWallboxError as err:
            raise UpdateFailed(str(err)) from err
        return {"ess": ess, "charger": charger}

    async def async_set_charging_mode(self, charging_mode: int) -> dict[str, Any]:
        """Set a mode and verify that AlphaESS persisted it."""
        return await self._async_write(self.api.async_set_charging_mode, charging_mode, "chargeMode")

    async def async_set_charging_current(self, amps: int) -> None:
        """Set and verify the maximum current per phase."""
        await self._async_write(self.api.async_set_charging_current, amps, "chargeCurrent")

    async def _async_write(self, write, value, field):
        # Both setters patch the same charger list. Serialize the entire read,
        # write and confirmation sequence so they preserve each other's values.
        async with self._charger_lock:
            result = await write(value)
            for attempt in range(5):
                if attempt:
                    await asyncio.sleep(3)
                ess = await self.api.async_get_ess()
                charger = self.api.get_charger(ess)
                if field == "chargeCurrent":
                    observed = read_charging_current(charger)
                else:
                    settings = charger.get("g1T")
                    try:
                        observed = int(settings.get(field)) if isinstance(settings, dict) else None
                    except (TypeError, ValueError):
                        observed = None
                if observed == value:
                    self.async_set_updated_data({"ess": ess, "charger": charger})
                    return result
            self.async_set_updated_data({"ess": ess, "charger": charger})
            raise AlphaESSWallboxError(f"AlphaESS did not confirm {field}={value}")
