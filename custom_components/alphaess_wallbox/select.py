"""Charging mode selector for AlphaESS Wallbox."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SYSTEM_SN, DOMAIN
from .coordinator import AlphaESSWallboxCoordinator

MODE_TO_OPTION = {
    1: "eco_slow",
    2: "eco_gentle",
    3: "eco_fast",
    4: "maximum_power",
}
OPTION_TO_MODE = {option: mode for mode, option in MODE_TO_OPTION.items()}


async def async_setup_entry(
    hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AlphaESSWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlphaESSWallboxChargingModeSelect(coordinator, entry)])


class AlphaESSWallboxChargingModeSelect(
    CoordinatorEntity[AlphaESSWallboxCoordinator], SelectEntity
):
    """Read and set the private-cloud wallbox charging mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging_mode"
    _attr_icon = "mdi:ev-station"
    _attr_options = list(OPTION_TO_MODE)

    def __init__(
        self, coordinator: AlphaESSWallboxCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        system_sn = entry.data[CONF_SYSTEM_SN]
        self._attr_unique_id = f"{entry.entry_id}_charging_mode_select"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, system_sn)},
            manufacturer="AlphaESS",
            model="Wallbox private Cloud API",
            name=f"AlphaESS Wallbox {system_sn}",
        )

    @property
    def current_option(self) -> str | None:
        charger = self.coordinator.data.get("charger")
        g1t = charger.get("g1T") if isinstance(charger, dict) else None
        if not isinstance(g1t, dict):
            return None
        try:
            mode = int(g1t.get("chargeMode"))
        except (TypeError, ValueError):
            return None
        return MODE_TO_OPTION.get(mode)

    async def async_select_option(self, option: str) -> None:
        mode = OPTION_TO_MODE.get(option)
        if mode is None:
            raise ValueError(f"Unsupported charging mode option: {option}")
        await self.coordinator.async_set_charging_mode(mode)
