# Changelog

All notable changes to this project are documented in this file.

# 0.4.2

## Added

- Populate the Home Assistant device with the charger model, serial number, software version, and hardware version returned by AlphaESS.

## Changed

- Share the dynamic charger device metadata between sensor and charging-mode select entities.

# 0.4.1

## Fixed

- Align the options-flow factory with the current Home Assistant API so reconfiguration opens correctly.

# 0.4.0

## Added

- Home Assistant options flow for changing credentials, the optional charger serial number, and the scan interval after setup.
- Reauthentication flow that prompts for updated credentials when AlphaESS rejects the stored login.
- English and German UI translations for reconfiguration and reauthentication.

## Changed

- Reload the integration automatically after saved option changes.
- Try the transformed and existing password values during login to improve compatibility with earlier configurations.

# 0.3.1

## Fixed

- Transform the normal AlphaESS account password as required by the platform login API.
- Keep compatibility with existing configurations that already contain the transformed password.

# 0.3.0

## Added

- Optional EV charger serial-number selection for systems with more than one charger.

## Changed

- Migrate to the current AlphaESS European platform API for authentication, charger discovery, status updates, and charging-mode control.
- Read the charging mode and device details from the selected charger in the ESS configuration.
- Preserve the complete charger configuration when changing the charging mode, then verify the persisted value.
- Update English and German configuration labels for the optional charger serial number.

# 0.2.2

## Fixed

- Restore the proven AlphaESS wallbox API endpoint and request payload for changing the charging mode.
- Avoid sending unnecessary wallbox configuration fields when applying a charging-mode change.

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
