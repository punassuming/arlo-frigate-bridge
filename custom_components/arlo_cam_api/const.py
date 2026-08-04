"""Constants for the Arlo Cam API integration."""

from __future__ import annotations

DOMAIN = "arlo_cam_api"
NAME = "Arlo Cam API"
PLATFORMS = ["sensor", "binary_sensor", "switch", "select", "button"]

CONF_BASE_URL = "base_url"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MQTT_PREFIX = "mqtt_prefix"
CONF_CAMERA_MAP = "camera_map"
CONF_MOTION_TAIL = "motion_tail_seconds"
CONF_MAX_ACTIVE = "max_active_seconds"

DEFAULT_BASE_URL = "http://192.168.50.100:5000"
DEFAULT_SCAN_INTERVAL = 300
DEFAULT_MQTT_PREFIX = "frigate"
DEFAULT_MOTION_TAIL = 15
DEFAULT_MAX_ACTIVE = 180

# Arlo cameras and arlo-cam-api must be on a trusted local network. Webhooks
# are intentionally not exposed through Home Assistant Cloud or a public proxy.
WEBHOOK_LOCAL_ONLY = True

WEBHOOK_KINDS = ("motion", "motion_timeout", "status", "registration", "button")
