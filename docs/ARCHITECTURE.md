# Architecture

```text
Arlo PIR → Arlo CAM API → local Home Assistant webhook → MQTT
         ↑                                               ↓
camera ← MediaMTX on-demand RTSP ← Frigate enabled camera
```

Arlo CAM API impersonates the base station and receives the camera PIR event.
Home Assistant maps the event serial to one Frigate camera and commands that
camera through MQTT. Frigate opens the MediaMTX path only while enabled;
MediaMTX is the only direct RTSP reader of the battery camera.

Arlo and Frigate remain separate Home Assistant devices. Place the matching
devices in one area or label; do not force device-registry merging.
