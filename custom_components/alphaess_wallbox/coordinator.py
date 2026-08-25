"""Coordinator for AlphaESS Wallbox."""

from __future__ import annotations

from datetime import timedelta
import asyncio
import logging
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlphaESSWallboxApi, AlphaESSWallboxError
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
            config = await self.api.async_get_wallbox_config()
            status = await self.api.async_get_wallbox_status()
        except AlphaESSWallboxError as err:
            raise UpdateFailed(str(err)) from err
        return {"config": config, "status": status}

    async def async_set_charging_mode(self, charging_mode: int) -> dict[str, Any]:
        """Set a mode and verify that AlphaESS persisted it."""
        result = await self.api.async_set_charging_mode(charging_mode)
        for _attempt in range(5):
            await asyncio.sleep(3)
            config = await self.api.async_get_wallbox_config()
            data = config.get("data")
            old_pile = data.get("oldPileData") if isinstance(data, dict) else None
            actual_mode = old_pile.get("chargingmode") if isinstance(old_pile, dict) else None
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
