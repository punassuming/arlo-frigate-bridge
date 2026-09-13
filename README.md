# Arlo Cam API for Home Assistant and Frigate

HACS integration and private deployment generator for battery-powered Arlo
cameras using Arlo CAM API, MediaMTX, Frigate, MQTT, and Home Assistant webhooks.

## What it provides

- Native Arlo hardware entities and controls in Home Assistant
- PIR-driven Frigate enable/disable with confirmed MQTT state
- Restart-safe battery timers and local-only webhooks
- A YAML inventory that renders the camera-host stack and a Frigate patch

## Install

Add `https://github.com/punassuming/hass-arlo-custom` to HACS as an
**Integration**, install it, restart Home Assistant, and add **Arlo Cam API**
from Settings → Devices & services.

Copy [`config/inventory.example.yaml`](config/inventory.example.yaml) to the
ignored `config/inventory.yaml`, then render private deployment files:

```bash
python -m pip install -r scripts/requirements.txt
python scripts/generate_deployment.py --inventory config/inventory.yaml \
  --output generated --bootstrap
```

Deploy that temporary camera-host configuration, create the Home Assistant
entry, copy its `entry_id` from the **Webhook paths** diagnostic entity, then
render the final webhook configuration:

```bash
python scripts/generate_deployment.py --inventory config/inventory.yaml \
  --output generated --home-assistant-entry-id YOUR_ENTRY_ID \
  --frigate-base /private/frigate/config.yml
```

## Boundaries

- Arlo CAM API and MediaMTX run on the camera-side host; Frigate remains a
  separate existing deployment.
- The integration owns hardware status, Arlo controls, webhooks, and the
  Frigate enable timer. Frigate owns video, detections, clips, and recordings.
- Frigate must consume the MediaMTX restream, never an Arlo camera directly.
- Arlo CAM API is unauthenticated: expose its API only to Home Assistant on the
  trusted LAN. Webhooks use Home Assistant's local-only protection.

See [architecture](docs/ARCHITECTURE.md), [installation](docs/INSTALLATION.md), [configuration](docs/CONFIGURATION.md),
[reference migration](docs/MIGRATION.md), [Frigate patching](docs/FRIGATE.md), [webhooks](docs/WEBHOOKS.md), and
[troubleshooting](docs/TROUBLESHOOTING.md).
