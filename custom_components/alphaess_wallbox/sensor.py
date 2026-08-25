"""Sensors for AlphaESS Wallbox."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SYSTEM_SN, DOMAIN
from .coordinator import AlphaESSWallboxCoordinator


@dataclass(frozen=True, kw_only=True)
class AlphaESSWallboxSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]]


def _mode(data: dict[str, Any]) -> Any:
    charger = data.get("charger")
    g1t = charger.get("g1T") if isinstance(charger, dict) else None
    return g1t.get("chargeMode") if isinstance(g1t, dict) else None


def _api_state(data: dict[str, Any]) -> str:
    return "connected" if isinstance(data.get("ess"), dict) else "error"


def _safe_status_attrs(data: dict[str, Any]) -> dict[str, Any]:
    charger = data.get("charger")
    attrs: dict[str, Any] = {}
    if isinstance(charger, dict):
        for key in ("sn", "model", "softwareVersion", "hardwareVersion", "phase"):
            if key in charger:
                attrs[key] = charger[key]
    return attrs


SENSORS = (
    AlphaESSWallboxSensorDescription(
        key="charging_mode",
        translation_key="charging_mode",
        icon="mdi:ev-station",
        value_fn=_mode,
        attrs_fn=lambda data: {},
    ),
    AlphaESSWallboxSensorDescription(
        key="api_status",
        translation_key="api_status",
        icon="mdi:cloud-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_api_state,
        attrs_fn=_safe_status_attrs,
    ),
)


async def async_setup_entry(
    hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AlphaESSWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AlphaESSWallboxSensor(coordinator, entry, description)
        for description in SENSORS
    )


class AlphaESSWallboxSensor(
    CoordinatorEntity[AlphaESSWallboxCoordinator], SensorEntity
):
    """A token-safe AlphaESS Wallbox sensor."""

    entity_description: AlphaESSWallboxSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AlphaESSWallboxCoordinator,
        entry: ConfigEntry,
        description: AlphaESSWallboxSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        system_sn = entry.data[CONF_SYSTEM_SN]
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, system_sn)},
            manufacturer="AlphaESS",
            model="Wallbox private Cloud API",
            name=f"AlphaESS Wallbox {system_sn}",
        )

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.entity_description.attrs_fn(self.coordinator.data)
