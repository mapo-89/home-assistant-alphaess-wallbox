"""Device metadata helpers for AlphaESS Wallbox."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def device_info(system_sn: str, data: dict[str, Any]) -> DeviceInfo:
    """Build device information from the current charger response."""
    charger = data.get("charger")
    if not isinstance(charger, dict):
        charger = {}

    charger_sn = str(charger.get("sn") or system_sn)
    model = str(charger.get("model") or "Wallbox")
    info = DeviceInfo(
        identifiers={(DOMAIN, system_sn)},
        manufacturer="AlphaESS",
        model=model,
        name=f"{model} ({charger_sn})",
        serial_number=charger_sn,
    )
    if software_version := charger.get("softwareVersion"):
        info["sw_version"] = str(software_version)
    if hardware_version := charger.get("hardwareVersion"):
        info["hw_version"] = str(hardware_version)
    return info
