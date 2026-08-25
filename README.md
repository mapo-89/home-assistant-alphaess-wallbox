# Home Assistant AlphaESS Wallbox

[![Version](https://img.shields.io/badge/version-0.2.2-03a9f4.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5.svg?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![GitHub issues](https://img.shields.io/github/issues/mapo-89/home-assistant-alphaess-wallbox.svg)](https://github.com/mapo-89/home-assistant-alphaess-wallbox/issues)
[![GitHub stars](https://img.shields.io/github/stars/mapo-89/home-assistant-alphaess-wallbox.svg)](https://github.com/mapo-89/home-assistant-alphaess-wallbox/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/mapo-89/home-assistant-alphaess-wallbox.svg)](https://github.com/mapo-89/home-assistant-alphaess-wallbox/commits/main)

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mapo-89&repository=home-assistant-alphaess-wallbox&category=integration)

An unofficial Home Assistant custom integration for reading and controlling an AlphaESS wallbox through the private AlphaESS cloud API.

> [!WARNING]
> This integration uses an undocumented private API. AlphaESS may change it without notice. This project is not affiliated with or endorsed by AlphaESS.

## Features

- Read the current charging mode.
- Change the charging mode directly in Home Assistant with a select entity, including ECO Slow, ECO Gentle charging, ECO Fast, and Maximum power.
- Display a token-safe API status and wallbox device information.
- Reconfigure credentials from the Home Assistant UI without restarting Home Assistant.
- Keep access and refresh tokens internal instead of exposing them in sensor attributes or command lines.
- English and German UI translations.

## Requirements

- Home Assistant 2026.3.0 or newer.
- An AlphaESS account with access to the ESS and wallbox.
- The ESS system serial number.

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Add `https://github.com/mapo-89/home-assistant-alphaess-wallbox` as a custom repository of type **Integration**.
3. Install **AlphaESS Wallbox**.
4. Restart Home Assistant after the first installation or after updating integration files.
5. Go to **Settings → Devices & services → Add integration** and search for **AlphaESS Wallbox**.

The button above can add the repository directly when My Home Assistant is configured.

### Manual installation

Copy `custom_components/alphaess_wallbox` to the `custom_components` directory in your Home Assistant configuration, then restart Home Assistant.

## Configuration

Enter the AlphaESS login email, the normal password used on the AlphaESS login page and the ESS system serial number. The integration performs the password transformation required by the current session API internally.

## Actions

The select entity is the preferred way to change the charging mode. Two actions are also available:

```yaml
action: alphaess_wallbox.set_charging_mode
data:
  charging_mode: 4
```

```yaml
action: alphaess_wallbox.refresh
```

When multiple config entries exist, also pass `config_entry_id`.

## Security

- Never post AlphaESS passwords, transformed passwords, tokens or complete session responses in an issue.
- Protect Home Assistant backups because config entries contain credentials.
- Rotate any credential that has previously appeared in logs, shell history, YAML or chat messages.
- See [SECURITY.md](SECURITY.md) for reporting guidance.

## Troubleshooting

Enable debug logging temporarily:

```yaml
logger:
  logs:
    custom_components.alphaess_wallbox: debug
```

Remove or disable debug logging after diagnosis and redact credentials, tokens and serial numbers before sharing logs.

## Development validation

```bash
python -m compileall -q custom_components/alphaess_wallbox
```

GitHub Actions additionally validates all JSON files on pushes and pull requests.

## License

MIT. See [LICENSE](LICENSE).

AlphaESS and related product names and logos are trademarks of their respective owners.

<a href="https://buymeacoffee.com/mapo"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=mapo&button_colour=FFDD00&font_colour=000000&font_family=Lato&outline_colour=000000&coffee_colour=ffffff" alt="Buy me a coffee"></a>
