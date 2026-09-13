# Mapping the working reference deployment

Use the local `arlo-cam-api/` folder only to populate private inventory values;
do not copy its databases, scripts, credentials, or literal webhook IDs.

| Reference file | Private inventory / generated result |
| --- | --- |
| `config.yaml` | `arlo_cam_api` defaults; generated webhook URLs replace literal IDs. |
| `mediamtx.yml` | Camera `address` values; generator applies the working UDP/on-demand/one-reader policy. |
| `frigate/config.yml` | `frigate.mqtt`, `frigate.baseline`, and each camera's detect/motion settings. |
| `docker-compose.yml` | `deployment` image pins and `camera_host` API binding; Frigate remains on its existing host. |
| `arlo_serials.json` | Each camera's private `serial`, `address`, and `id`. |
| `webhooks.yaml` | Not migrated; generated entry-based paths replace it. |
| `camera_off.sh` | Not migrated; Home Assistant restart safety publishes the off commands. |

Start from `inventory.example.yaml`, transfer every global Frigate setting into
`frigate.baseline`, then transfer each Arlo camera's serial, address, detection
dimensions, FPS, and motion mask. Generate a patch, merge it against a private
copy of the existing Frigate config, compare it with the working configuration,
and validate before deployment.
