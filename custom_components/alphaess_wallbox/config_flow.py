"""Config flow for AlphaESS Wallbox."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AlphaESSWallboxApi,
    AlphaESSWallboxAuthError,
    AlphaESSWallboxConnectionError,
    AlphaESSWallboxError,
)
from .const import (
    CONF_CHARGING_PILE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_SN,
    DEFAULT_CHARGING_PILE_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class AlphaESSWallboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure AlphaESS Wallbox through the UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            system_sn = user_input[CONF_SYSTEM_SN].strip()
            await self.async_set_unique_id(system_sn)
            self._abort_if_unique_id_configured()

            api = AlphaESSWallboxApi(
                async_get_clientsession(self.hass),
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                system_sn,
                user_input[CONF_CHARGING_PILE_ID].strip(),
            )
            try:
                await api.async_validate()
            except AlphaESSWallboxAuthError:
                errors["base"] = "invalid_auth"
            except AlphaESSWallboxConnectionError:
                errors["base"] = "cannot_connect"
            except AlphaESSWallboxError:
                errors["base"] = "unknown"
            else:
                data = dict(user_input)
                data[CONF_SYSTEM_SN] = system_sn
                data[CONF_CHARGING_PILE_ID] = user_input[CONF_CHARGING_PILE_ID].strip()
                return self.async_create_entry(title=f"AlphaESS Wallbox {system_sn}", data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SYSTEM_SN): str,
                vol.Required(
                    CONF_CHARGING_PILE_ID, default=DEFAULT_CHARGING_PILE_ID
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

