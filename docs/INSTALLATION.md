# Installation

## 1. Network and camera prerequisites

`arlo-cam-api` impersonates an Arlo base station. Cameras connect to TCP 4000;
audio doorbells use TCP 4100. Configure routing or destination NAT so the
camera network can reach the host running `arlo-cam-api` on those ports.

Keep these services on a trusted internal network:

- Allow Home Assistant to reach `arlo-cam-api` on TCP 5000.
- Allow the Arlo host to reach Home Assistant on TCP 8123 for webhooks.
- Do not expose TCP 5000 or webhook URLs to the internet.

## 2. Create a private inventory

```bash
cp config/inventory.example.json config/inventory.json
```

Edit `config/inventory.json` with your own camera host/IP addresses, serial
numbers, MQTT credentials, and service hostnames. This file is Git-ignored.
Camera `id` values must be unique lowercase identifiers using letters, numbers,
and underscores; they become the Frigate and MediaMTX path names.

## 3. Install through HACS

1. Open HACS → **Integrations**.
2. Add `https://github.com/punassuming/hass-arlo-custom` as an **Integration**
   custom repository.
3. Install **Arlo Cam API** and restart Home Assistant.
4. Add **Arlo Cam API** from **Settings → Devices & services**.
5. Enter the private `arlo-cam-api` URL from your inventory.

## 4. Generate configuration

Find the config-entry ID in the Arlo Cam API webhook-path entity attributes,
then run:

```bash
python scripts/generate_deployment.py \
  --inventory config/inventory.json \
  --output generated \
  --home-assistant-entry-id YOUR_ENTRY_ID
```

Copy the generated files into the respective service configuration locations:

- `generated/arlo-cam-api/config.yaml`
- `generated/mediamtx/mediamtx.yml`
- `generated/frigate/config.yml`

Use `generated/home-assistant/options.json` as the values for the integration's
**Configure** dialog. The serial-to-camera map and MQTT prefix must match the
generated Frigate configuration exactly.

## 5. Start and validate

Create the `arlo-cam-api` database and start the containers using the supplied
Docker Compose file:

```bash
touch arlo-cam-api/arlo.db
docker compose up -d
curl -s http://ARLO_CAM_API_HOST:5000/device | jq
```

Then trigger a camera PIR event and follow the four-boundary workflow in
[Troubleshooting](TROUBLESHOOTING.md). It verifies camera motion, webhook
delivery, Frigate MQTT confirmation, and MediaMTX streaming separately.

## 6. Pair with Frigate devices

Home Assistant does not safely merge devices owned by different integrations.
Assign matching Arlo and Frigate devices to the same area or label. Keep entity
IDs distinct: Frigate owns video/object entities, while Arlo owns battery,
hardware status, and controls.
