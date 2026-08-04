"""Config flow for Arlo Cam API."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ArloCamApiClient, ArloCamApiError
from .const import (
    CONF_BASE_URL,
    CONF_CAMERA_MAP,
    CONF_MAX_ACTIVE,
    CONF_MOTION_TAIL,
    CONF_MQTT_PREFIX,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_ACTIVE,
    DEFAULT_MOTION_TAIL,
    DEFAULT_MQTT_PREFIX,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NAME,
)


def _normalize_base_url(value: str) -> str:
    """Accept only a direct, credential-free local API URL."""
    url = value.strip().rstrip("/")
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise vol.Invalid("expected a credential-free http(s) URL")
    return url


def _normalize_mqtt_prefix(value: str) -> str:
    """Reject MQTT wildcards and malformed topic prefixes."""
    prefix = value.strip().strip("/")
    if not prefix or "+" in prefix or "#" in prefix or "//" in prefix:
        raise ValueError("invalid MQTT prefix")
    return prefix


def _parse_camera_map(value: str) -> dict[str, str]:
    """Parse an explicit one-to-one Arlo serial to Frigate camera mapping."""
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("camera map is not an object")

    result: dict[str, str] = {}
    used_names: set[str] = set()
    for serial, camera in parsed.items():
        normalized_serial = str(serial).strip()
        normalized_camera = str(camera).strip()
        if (
            not normalized_serial
            or not normalized_camera
            or "/" in normalized_camera
            or "+" in normalized_camera
            or "#" in normalized_camera
            or normalized_camera in used_names
        ):
            raise ValueError("invalid camera map entry")
        result[normalized_serial] = normalized_camera
        used_names.add(normalized_camera)
    return result


class ArloCamApiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                base_url = _normalize_base_url(str(user_input[CONF_BASE_URL]))
            except vol.Invalid:
                errors[CONF_BASE_URL] = "invalid_url"
                base_url = ""
            client = ArloCamApiClient(async_get_clientsession(self.hass), base_url)
            if not errors:
                try:
                    await client.list_devices()
                except ArloCamApiError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(base_url.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=NAME, data={CONF_BASE_URL: base_url})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str}
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ArloCamApiOptionsFlow(config_entry)


class ArloCamApiOptionsFlow(config_entries.OptionsFlow):
    """Manage polling, MQTT, and camera mapping."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                camera_map = _parse_camera_map(user_input[CONF_CAMERA_MAP])
            except (json.JSONDecodeError, ValueError):
                errors[CONF_CAMERA_MAP] = "invalid_json"
            else:
                try:
                    mqtt_prefix = _normalize_mqtt_prefix(user_input[CONF_MQTT_PREFIX])
                except ValueError:
                    errors[CONF_MQTT_PREFIX] = "invalid_mqtt_prefix"
                if user_input[CONF_MAX_ACTIVE] < user_input[CONF_MOTION_TAIL]:
                    errors[CONF_MAX_ACTIVE] = "max_active_too_short"
                if not errors:
                    data = dict(user_input)
                    data[CONF_CAMERA_MAP] = json.dumps(camera_map, sort_keys=True)
                    data[CONF_MQTT_PREFIX] = mqtt_prefix
                    return self.async_create_entry(title="", data=data)

        options = self.entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(int, vol.Range(min=30, max=3600)),
                    vol.Required(
                        CONF_MQTT_PREFIX,
                        default=options.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX),
                    ): str,
                    vol.Required(
                        CONF_CAMERA_MAP,
                        default=options.get(CONF_CAMERA_MAP, "{}"),
                    ): str,
                    vol.Required(
                        CONF_MOTION_TAIL,
                        default=options.get(CONF_MOTION_TAIL, DEFAULT_MOTION_TAIL),
                    ): vol.All(int, vol.Range(min=0, max=600)),
                    vol.Required(
                        CONF_MAX_ACTIVE,
                        default=options.get(CONF_MAX_ACTIVE, DEFAULT_MAX_ACTIVE),
                    ): vol.All(int, vol.Range(min=30, max=3600)),
                }
            ),
            errors=errors,
        )
