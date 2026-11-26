"""Maximum charging current per phase in AlphaESS Wallbox."""
from math import isfinite

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AlphaESSWallboxError, read_charging_current
from .const import CONF_SYSTEM_SN, DOMAIN
from .device import device_info


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlphaESSWallboxChargingCurrent(coordinator, entry)])


class AlphaESSWallboxChargingCurrent(CoordinatorEntity, NumberEntity):
    """Wallbox setpoint independent of the household current setting."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging_current"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_native_min_value = 6
    _attr_native_max_value = 16
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_charging_current"
        self._attr_device_info = device_info(entry.data[CONF_SYSTEM_SN], coordinator.data)

    @property
    def native_value(self):
        return read_charging_current((self.coordinator.data or {}).get("charger"))

    @property
    def available(self):
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self):
        charger = (self.coordinator.data or {}).get("charger") or {}
        raw = charger.get("houseHoldCurrent")
        if isinstance(raw, bool):
            return {}
        try:
            amps = float(raw)
        except (TypeError, ValueError):
            return {}
        return {"household_current_a": amps} if isfinite(amps) and amps > 0 else {}

    async def async_set_native_value(self, value):
        if not isfinite(value) or not 6 <= value <= 16 or value != int(value):
            raise HomeAssistantError("Charging current must be a whole number from 6 to 16 A")
        try:
            await self.coordinator.async_set_charging_current(int(value))
        except AlphaESSWallboxError as err:
            raise HomeAssistantError(str(err)) from err
