# Private inventory

`config/inventory.yaml` is the deployment source of truth and is Git-ignored.
The example file contains the full schema and the current working defaults.

- `deployment` pins the Arlo CAM API and MediaMTX images.
- `camera_host` is the address on which the local Arlo API is reachable by Home
  Assistant. Firewall it to Home Assistant only.
- `home_assistant.internal_url` must resolve from the camera host; do not use a
  public proxy URL.
- `frigate.baseline` carries the existing detector, model, recording, snapshot,
  acceleration, and recognition settings into the generated patch.
- Each camera defines the Frigate/MediaMTX ID, Arlo serial, camera address,
  detection dimensions/FPS, and optional motion masks.

Runtime data such as `arlo.db`, Frigate databases, recordings, model caches,
and discovered serial exports are not inventory and are never generated.
