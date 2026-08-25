"""Config flow for AlphaESS Wallbox."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AlphaESSWallboxApi,
    AlphaESSWallboxAuthError,
    AlphaESSWallboxConnectionError,
    AlphaESSWallboxError,
)
from .const import (
    CONF_CHARGER_SN,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_SN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class AlphaESSWallboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure AlphaESS Wallbox through the UI."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> AlphaESSWallboxOptionsFlow:
        """Return the options flow handler."""
        return AlphaESSWallboxOptionsFlow()

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
                user_input.get(CONF_CHARGER_SN, "").strip() or None,
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
                data[CONF_CHARGER_SN] = user_input.get(CONF_CHARGER_SN, "").strip()
                return self.async_create_entry(title=f"AlphaESS Wallbox {system_sn}", data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SYSTEM_SN): str,
                vol.Optional(CONF_CHARGER_SN, default=""): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Start reauthentication after AlphaESS rejects a login."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Validate and save replacement credentials."""
        entry = self._get_reauth_entry()
        current = {**entry.data, **entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            updated = {
                **entry.data,
                **entry.options,
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            errors = await _validate_input(self.hass, updated)
            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry, data=updated, options={}
                )
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME, default=current[CONF_USERNAME]
                ): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=schema, errors=errors
        )


class AlphaESSWallboxOptionsFlow(config_entries.OptionsFlow):
    """Allow credentials and mutable wallbox settings to be changed."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Validate changed settings before storing them."""
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}

        if user_input is not None:
            updated = {
                **current,
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD) or current[CONF_PASSWORD],
                CONF_CHARGER_SN: user_input.get(CONF_CHARGER_SN, "").strip(),
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
            }
            errors = await _validate_input(self.hass, updated)
            if not errors:
                return self.async_create_entry(title="", data=updated)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME, default=current[CONF_USERNAME]
                ): str,
                vol.Optional(CONF_PASSWORD, default=""): str,
                vol.Optional(
                    CONF_CHARGER_SN,
                    default=current.get(CONF_CHARGER_SN, ""),
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )


async def _validate_input(hass, data: dict[str, Any]) -> dict[str, str]:
    """Validate one complete set of configuration values."""
    api = AlphaESSWallboxApi(
        async_get_clientsession(hass),
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        data[CONF_SYSTEM_SN],
        data.get(CONF_CHARGER_SN) or None,
    )
    try:
        await api.async_validate()
    except AlphaESSWallboxAuthError:
        return {"base": "invalid_auth"}
    except AlphaESSWallboxConnectionError:
        return {"base": "cannot_connect"}
    except AlphaESSWallboxError:
        return {"base": "unknown"}
    return {}
