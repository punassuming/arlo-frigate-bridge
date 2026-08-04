# Arlo Cam API for Home Assistant and Frigate

HACS-installable Home Assistant integration and deployment generator for local
Arlo battery cameras using `brianschrameck/arlo-cam-api`, MediaMTX, Frigate,
MQTT, and Home Assistant webhooks.

## What it provides

- Arlo battery, hardware-status, and control entities
- Motion-driven Frigate enable/disable through MQTT
- Confirmed Frigate MQTT state rather than optimistic commands
- Battery-safe post-motion and maximum-active timers
- Generated Arlo, MediaMTX, Frigate, and Home Assistant options from one
  private inventory file

## Install

Add this repository to HACS as a custom repository of type **Integration**:

```text
https://github.com/punassuming/hass-arlo-custom
```

Then follow [the complete installation guide](docs/INSTALLATION.md).

## Private deployment inventory

No camera addresses, serial numbers, names, credentials, or network topology
are stored in this repository. Copy
[`config/inventory.example.json`](config/inventory.example.json) to
`config/inventory.json`, fill it with your own values, and keep that file
private. It is ignored by Git.

After installing the integration, generate all deployment files with:

```bash
python scripts/generate_deployment.py \
  --inventory config/inventory.json \
  --output generated \
  --home-assistant-entry-id YOUR_ENTRY_ID
```

The command creates configuration for Arlo Cam API, MediaMTX, Frigate, and
Home Assistant integration options under `generated/`.

## Important boundaries

- The upstream REST API is unauthenticated. Restrict TCP 5000 to Home Assistant
  and administrative hosts.
- Keep the private inventory and generated directory out of source control.
- The integration controls Frigate only through MQTT; it does not wake an Arlo
  battery camera. PIR motion must reach `arlo-cam-api` first.
- Do not force Arlo entities into Frigate's device-registry entry; assign both
  devices to the same Home Assistant area or label instead.

## Documentation

- [Installation and generated deployment](docs/INSTALLATION.md)
- [Control behavior and audio](docs/CONTROLS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## License

MIT
