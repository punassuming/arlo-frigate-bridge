# Installation and migration

## Prerequisites

Route or destination-NAT camera traffic to the camera host on TCP/UDP 4000 and,
where applicable, TCP/UDP 4100. Allow Home Assistant to reach the Arlo CAM API
on the configured trusted-LAN address and port. Allow the camera host to reach
Home Assistant's **internal** URL on TCP 8123.

Install Arlo Frigate Bridge through HACS, restart Home Assistant, and create its
config entry. Copy the serial-to-camera map and MQTT prefix from the generated
`home-assistant/options.json` into the integration Configure dialog.

## Generate and deploy

Copy `config/inventory.example.yaml` to ignored `config/inventory.yaml`, fill
it with the working deployment values, then render a temporary camera-host
deployment before the Home Assistant entry exists:

```bash
python -m pip install -r scripts/requirements.txt
python scripts/generate_deployment.py --inventory config/inventory.yaml \
  --output generated --bootstrap
```

Deploy `generated/camera-host/`, then add the integration using
`http://CAMERA_HOST:API_PORT`. In Developer Tools → States, open the
**Arlo Frigate Bridge Webhook paths** diagnostic entity and copy its `entry_id`
attribute. Render the final files with that ID:

```bash
python scripts/generate_deployment.py --inventory config/inventory.yaml \
  --output generated --home-assistant-entry-id YOUR_ENTRY_ID \
  --frigate-base /private/frigate/config.yml
```

Replace the temporary camera-host files with the final files and restart that
stack. Review and validate the private `generated/frigate/config.yml` on the
existing Frigate host before reloading Frigate. Keep the generated manifest
with the deployed files.

## Cut over safely

Migrate one camera first. Confirm motion triggers Frigate, the stream opens,
recording completes, and Frigate turns off after the timeout. Then remove the
matching entities/automations from the legacy packages. Remove both legacy
packages after every camera has migrated; they must not run alongside this
integration.
