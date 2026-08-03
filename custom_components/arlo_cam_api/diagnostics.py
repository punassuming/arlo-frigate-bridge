"""Diagnostics support for Arlo Cam API."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_BASE_URL, DOMAIN
from .coordinator import ArloRuntime

TO_REDACT = {CONF_BASE_URL, "ip"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    runtime: ArloRuntime = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "cameras": async_redact_data(runtime.coordinator.data or {}, TO_REDACT),
        "frigate_active": dict(runtime.frigate_active),
    }
