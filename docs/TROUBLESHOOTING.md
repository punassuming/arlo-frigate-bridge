# Troubleshooting

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

- Inspect `sensor.arlo_cam_api_webhook_paths`.
- Confirm the exact URLs are in `arlo-cam-api/config.yaml`.
- Set `NotifyOnMotionAlert: true` and `NotifyOnMotionTimeoutAlert: true`.
- Verify the serial-to-camera JSON mapping.
- Subscribe to `frigate/+/enabled/set` in Home Assistant MQTT diagnostics.

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
