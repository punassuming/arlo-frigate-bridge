# Battery-safe webhook behavior

The generator derives webhook paths from the Home Assistant config-entry ID:
motion, motion timeout, status, and registration. It enables Arlo CAM API
motion/timeout/status notifications and keeps audio/button notifications off.

| Event | Result |
| --- | --- |
| PIR motion | Enable only the mapped Frigate camera and reset the safety timer. |
| Motion timeout | Replace the safety timer with the recording tail. |
| Timer expiry | Disable the mapped Frigate camera. |
| Home Assistant or Frigate restart | Cancel timers and command every mapped camera off. |

Unknown serials are ignored. Status and registration webhooks refresh cached
state; they do not wake cameras.
