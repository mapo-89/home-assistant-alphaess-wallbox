# Changelog

All notable changes to this project are documented in this file.

# 0.2.1

## Fixed

- Send wallbox configuration and charging-mode changes to the current AlphaESS cloud endpoint so changes persist in the AlphaESS app and on the charger.

# 0.2.0

## Added

- A Home Assistant select entity for changing the wallbox charging mode directly from the UI.
- Four named charging-mode options: ECO Slow, ECO Gentle charging, ECO Fast, and Maximum power.
- English and German translations for the charging-mode selector and its options.

# 0.1.1

- Bugfix: Fixes a bug that caused the integration to fail when the wallbox was not connected to the ESS system.

# 0.1.0

- AlphaESS Wallbox integration with configuration, API client, and sensor support.
