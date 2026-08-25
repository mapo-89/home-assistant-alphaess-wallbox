"""Constants for the AlphaESS Wallbox integration."""

DOMAIN = "alphaess_wallbox"

CONF_SYSTEM_SN = "system_sn"
CONF_CHARGING_PILE_ID = "charging_pile_id"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_CHARGING_PILE_ID = "EV1"
DEFAULT_SCAN_INTERVAL = 20

SERVICE_SET_CHARGING_MODE = "set_charging_mode"
SERVICE_REFRESH = "refresh"

PLATFORMS = ["sensor", "select"]
