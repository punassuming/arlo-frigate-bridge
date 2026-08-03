"""Config flow for Arlo Cam API."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
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


class ArloCamApiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = str(user_input[CONF_BASE_URL]).rstrip("/")
            client = ArloCamApiClient(async_get_clientsession(self.hass), base_url)
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
                parsed = json.loads(user_input[CONF_CAMERA_MAP])
                if not isinstance(parsed, dict):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                errors[CONF_CAMERA_MAP] = "invalid_json"
            else:
                return self.async_create_entry(title="", data=user_input)

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
