# Troubleshooting

## Troubleshoot a camera that responds to MQTT but does not wake on motion

MQTT cannot wake a battery Arlo camera. It only enables Frigate *after* the
camera PIR has detected motion and `arlo-cam-api` has delivered a motion
webhook. Test each boundary in order; do not start with Frigate.

### 1. Prove camera-to-API motion

Trigger PIR motion and watch the API container:

```bash
docker logs -f arlo-cam-api
```

You must see a motion event. If not, check that the camera is registered,
`PIRTargetState` is `Armed`, Wi-Fi signal is strong, and the camera VLAN can
reach the emulated base station on TCP 4000. MQTT settings cannot repair this
stage.

If the camera was previously streaming and now ignores motion, stop every live
viewer, Frigate/go2rtc reader, VLC session, and RTSP test client. A battery
camera can remain stuck after an RTSP client fails to send a teardown. Reboot
the camera (or remove its battery briefly) and test with exactly one reader.

### 2. Prove API-to-Home-Assistant webhook delivery

The API log should show an HTTP `200` response for the configured motion URL.
Then inspect Home Assistant logs for `arlo_cam_api`. The URL must target the
internal Home Assistant address and use the `motion` webhook ID exposed by
`sensor.arlo_cam_api_webhook_paths`. Public proxies and Home Assistant Cloud
URLs are intentionally rejected.

### 3. Prove Home-Assistant-to-Frigate MQTT delivery

Subscribe before causing another motion event:

```bash
mosquitto_sub -v -t 'frigate/+/enabled/#'
```

Expect both a command and confirmation, for example:

```text
frigate/arlo_porch/enabled/set ON
frigate/arlo_porch/enabled/state ON
```

If `set` appears without `state`, verify that the broker, Frigate
`topic_prefix`, and exact camera name in the integration's serial-to-camera
map agree. The integration's Frigate switch reports the confirmed `state`, not
just the requested command.

### 4. Prove Frigate-to-MediaMTX streaming

Only after the state is `ON`, watch both logs:

```bash
docker logs -f frigate
docker logs -f mediamtx
```

There should be one MediaMTX source connection to the Arlo camera. If it is
immediately closed or repeatedly reconnects, inspect RTSP transport and VLAN
firewall rules. Do not leave a Frigate live view or any second RTSP reader
open while testing, since it can keep the battery camera awake even when the
Frigate camera is disabled.

## Camera appears in arlo-cam-api but Frigate has no frames

1. Confirm MediaMTX can reach `rtsp://CAMERA_IP/live`.
2. Confirm the MediaMTX path uses `sourceOnDemand: yes` and `rtspAnyPort: yes`.
3. Confirm only one process connects directly to the camera.
4. Inspect MediaMTX logs for RTSP timeout.
5. Confirm Frigate reads the MediaMTX/go2rtc restream rather than the camera IP.

## Home Assistant entities are unavailable

- Test `curl http://ARLO_HOST:5000/device` from the Home Assistant network.
- Check firewall policy between Home Assistant and the Arlo host.
- Confirm port 5000 is not bound only to loopback.
- Reload the integration after pairing a new camera; platforms create entities from the cameras present during setup.

## Motion does not enable Frigate

- Follow the four boundary checks above.
- Set `NotifyOnMotionAlert: true`; do not rely on the upstream timeout webhook.
- Verify the serial-to-camera JSON mapping uses the exact Frigate camera name.
- Check both `frigate/+/enabled/set` and `frigate/+/enabled/state`.

## Spotlight still turns on

- Confirm **Motion spotlight** is off.
- Confirm **Infrared night vision** remains on.
- Reconnect or reboot the camera if it registered before the setting was saved.
- Check status for `NightModeLightSourceAlert` and `PIRAction` when provided by the model.

## No audio

- Turn on the camera **Microphone** switch.
- Verify the source stream actually contains audio with `ffprobe`.
- Use the AAC recording preset.
- Use go2rtc for live audio; jsmpeg fallback has no audio.
