# Arlo Cam API for Home Assistant and Frigate

HACS-installable Home Assistant integration and complete reference deployment for local Arlo battery cameras using `brianschrameck/arlo-cam-api`, MediaMTX, Frigate, MQTT, and Home Assistant webhooks.

## What it provides

- Battery percentage and voltage
- Temperature, Wi-Fi RSSI, signal indicator, firmware, and failed-stream diagnostics
- Charging, critical-battery, infrared-active, and spotlight-active sensors
- Motion arming and PIR indicator LED controls
- Microphone and speaker-enable controls
- Visible motion spotlight policy independent of infrared night vision
- Video quality selection
- Cached status refresh and explicit camera status request
- Automatic Frigate enable/disable through MQTT on Arlo motion webhooks
- Safety timeout and post-motion recording tail
- Complete Docker, MediaMTX, Frigate, Home Assistant, dashboard, notification, VLAN, and troubleshooting examples

## Install

Add this repository to HACS as a custom repository of type **Integration**:

```text
https://github.com/punassuming/hass-arlo-custom
```

Then follow [the complete installation guide](docs/INSTALLATION.md).

## Three-camera reference

| Camera | Camera IP | Known serial | Frigate name |
|---|---:|---|---|
| Gate | `172.14.1.174` | replace | `arlo_gate` |
| Garage | `172.14.1.97` | replace | `arlo_garage` |
| Porch | `172.14.1.78` | `AAE3177HA59AC` | `arlo_porch` |

## Important boundaries

- The upstream REST API is unauthenticated. Restrict TCP 5000 to Home Assistant and administrative hosts.
- The visible spotlight and infrared LEDs are separate. Disabling motion spotlight does not disable infrared night vision.
- Speaker enable is not two-way talk.
- Frigate audio detection only runs while PIR motion has already woken and enabled the stream.
- Do not force Arlo entities into Frigate's device-registry entry; assign both devices to the same Home Assistant area/label instead.

## Documentation

- [Installation and full deployment](docs/INSTALLATION.md)
- [Control behavior and audio](docs/CONTROLS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## License

MIT
