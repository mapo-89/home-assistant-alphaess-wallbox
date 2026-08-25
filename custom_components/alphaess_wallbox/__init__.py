"""AlphaESS Wallbox private Cloud API integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AlphaESSWallboxApi, AlphaESSWallboxError
from .const import (
    CONF_CHARGER_SN,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_SN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_REFRESH,
    SERVICE_SET_CHARGING_MODE,
)
from .coordinator import AlphaESSWallboxCoordinator

SET_MODE_SCHEMA = vol.Schema(
    {
        vol.Optional("config_entry_id"): cv.string,
        vol.Required("charging_mode"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
    }
)
REFRESH_SCHEMA = vol.Schema({vol.Optional("config_entry_id"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AlphaESS Wallbox from a config entry."""
    config = {**entry.data, **entry.options}
    api = AlphaESSWallboxApi(
        async_get_clientsession(hass),
        config[CONF_USERNAME],
        config[CONF_PASSWORD],
        config[CONF_SYSTEM_SN],
        config.get(CONF_CHARGER_SN),
    )
    coordinator = AlphaESSWallboxCoordinator(
        hass, api, config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CHARGING_MODE):
        async def async_set_mode(call: ServiceCall) -> None:
            coordinator_for_call = _resolve_coordinator(hass, call.data.get("config_entry_id"))
            try:
                await coordinator_for_call.async_set_charging_mode(call.data["charging_mode"])
            except AlphaESSWallboxError as err:
                raise HomeAssistantError(str(err)) from err

        async def async_refresh(call: ServiceCall) -> None:
            coordinator_for_call = _resolve_coordinator(hass, call.data.get("config_entry_id"))
            await coordinator_for_call.async_request_refresh()

        hass.services.async_register(
            DOMAIN, SERVICE_SET_CHARGING_MODE, async_set_mode, schema=SET_MODE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, SERVICE_REFRESH, async_refresh, schema=REFRESH_SCHEMA
        )
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an AlphaESS Wallbox config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    hass.data[DOMAIN].pop(entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_SET_CHARGING_MODE)
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
        hass.data.pop(DOMAIN)
    return True


def _resolve_coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> AlphaESSWallboxCoordinator:
    entries = hass.data.get(DOMAIN, {})
    if entry_id:
        coordinator = entries.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError("Unknown AlphaESS Wallbox config entry")
        return coordinator
    if len(entries) != 1:
        raise HomeAssistantError(
            "config_entry_id is required when multiple AlphaESS Wallbox entries exist"
        )
    return next(iter(entries.values()))
