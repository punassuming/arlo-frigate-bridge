"""Video quality selection."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ArloRuntime
from .entity import ArloEntity

OPTIONS = ["low", "medium", "high", "subscription", "insane"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime: ArloRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(ArloQualitySelect(runtime, serial) for serial in (runtime.coordinator.data or {}))


class ArloQualitySelect(ArloEntity, SelectEntity):
    _attr_name = "Video quality"
    _attr_options = OPTIONS
    _attr_icon = "mdi:video-high-definition"

    def __init__(self, runtime: ArloRuntime, serial: str) -> None:
        super().__init__(runtime, serial)
        self._attr_unique_id = f"{serial}_video_quality"
        self._current = "insane"

    @property
    def current_option(self) -> str:
        return self._current

    async def async_select_option(self, option: str) -> None:
        if option not in OPTIONS:
            return
        if await self.runtime.client.set_quality(self.serial, option):
            self._current = option
            self.async_write_ha_state()
