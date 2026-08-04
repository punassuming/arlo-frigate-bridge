# Installation

## 1. Network and camera prerequisites

`arlo-cam-api` impersonates an Arlo base station. Cameras connect to TCP 4000; audio doorbells use TCP 4100. The camera VLAN gateway usually needs destination NAT to the host running `arlo-cam-api`, and some models also require source NAT so replies appear to originate from the camera gateway.

Recommended segmentation:

- Camera VLAN: `172.14.1.0/24`, gateway `172.14.1.1`
- Home Assistant: `192.168.50.172`
- Arlo/MediaMTX host: fixed LAN address
- Allow Home Assistant to reach the Arlo host on TCP 5000
- Allow the Arlo host to reach Home Assistant TCP 8123
- Do not expose TCP 5000 to the internet

## 2. Start arlo-cam-api and MediaMTX

Copy `examples/docker-compose.yml`, `examples/arlo-cam-api/config.yaml`, and `examples/mediamtx/mediamtx.yml` into one directory. Create the database before startup:

```bash
touch arlo-cam-api/arlo.db
docker compose up -d
```

Confirm the cameras are registered:

```bash
curl -s http://ARLO_HOST:5000/device | jq
```

The example maps the known camera IPs as:

- Gate: `172.14.1.174`
- Garage: `172.14.1.97`
- Porch: `172.14.1.78`, serial `AAE3177HA59AC`

Replace the two unknown serials after reading `/device`.

## 3. Install through HACS

1. Open HACS.
2. Open **Integrations**.
3. Add custom repository `https://github.com/punassuming/hass-arlo-custom` as type **Integration**.
4. Install **Arlo Cam API**.
5. Restart Home Assistant.
6. Open **Settings > Devices & services > Add integration > Arlo Cam API**.
7. Enter `http://ARLO_HOST:5000`.

## 4. Configure camera-to-Frigate mapping

Open the integration's **Configure** dialog and enter JSON mapping serials to the exact Frigate camera names:

```json
{
  "REPLACE_GATE_SERIAL": "arlo_gate",
  "REPLACE_GARAGE_SERIAL": "arlo_garage",
  "AAE3177HA59AC": "arlo_porch"
}
```

Keep the MQTT prefix at `frigate` unless Frigate uses another `topic_prefix`.

## 5. Configure webhooks

Open the entity named **Arlo Cam API Webhook paths**. Copy only the `motion`
and `status` attributes into `arlo-cam-api/config.yaml`, prefixed with the
internal Home Assistant URL, for example:

```text
http://192.168.50.172:8123/api/webhook/arlo_cam_api_<entry-id>_motion
```

Restart `arlo-cam-api` after replacing the two webhook placeholders. The
integration accepts webhooks only from the local network; do not route these
URLs through Home Assistant Cloud or a public reverse proxy.

## 6. Configure Frigate

Merge `examples/frigate/config.yml` into your existing Frigate configuration.
Camera names must match the integration mapping exactly. Each camera starts
with `enabled: false`; a valid Arlo motion webhook publishes `ON` to
`frigate/<camera>/enabled/set`. The integration owns the post-motion tail and
maximum-active timers, rather than depending on unsupported upstream timeout
webhooks. It also subscribes to `frigate/<camera>/enabled/state`; this is the
authoritative confirmation that Frigate applied the command.

## 7. Pair with existing Frigate devices

Home Assistant does not safely merge devices owned by different integrations. Assign the matching Arlo and Frigate devices to the same **Area** and optionally the same label:

- Gate Camera
- Garage Camera
- Porch Camera

Keep entity IDs distinct. The Frigate device owns video/object entities; the Arlo device owns battery, hardware status, and camera controls.

## 8. Validate

```bash
curl -s http://ARLO_HOST:5000/device/AAE3177HA59AC | jq
```

In Home Assistant, verify:

- Battery and voltage populate without requesting a new camera status.
- Turning **Motion spotlight** off leaves **Infrared night vision** on.
- Turning **Microphone** on allows audio in Frigate recordings/live view.
- A PIR event enables the corresponding Frigate camera.
- A motion timeout disables it after the configured tail.
