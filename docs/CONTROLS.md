# Controls and behavior

## Spotlight versus infrared

The integration deliberately separates the visible white spotlight from infrared night vision.

Turning **Motion spotlight** off sends:

```json
{
  "NightModeLightSourceAlert": 0,
  "NightVisionMode": true,
  "PIRAction": "Stream"
}
```

Turning it on sends `NightModeLightSourceAlert: 1` and `PIRAction: Stream+Spotlight`. This changes future motion behavior. It is not a verified immediate manual lamp-off command.

## Audio

**Microphone** sets `AudioMicEnable`. Audio retention and browser-live audio are
Frigate deployment concerns and are deliberately not enabled by the battery
camera patch unless the private Frigate baseline adds an audio role.

**Speaker enabled** only toggles `AudioSpkrEnable`. It does not implement two-way talk or feed audio back to the camera.

Native audio-triggered wake is intentionally excluded because upstream audio-alert webhook processing is unfinished and frequent sound wakes can drain batteries.

## Battery-safe refresh behavior

**Refresh cached status** rereads the local `arlo-cam-api` database and does not contact the camera directly.

**Request camera status** calls `/statusrequest`; use it sparingly because it can require the camera to be awake and its upstream result may be false while cached status remains valid.
