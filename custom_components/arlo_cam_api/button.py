"""Refresh controls."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ArloRuntime
from .entity import ArloEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime: ArloRuntime = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []
    for serial in (runtime.coordinator.data or {}):
        entities.extend([ArloRefreshButton(runtime, serial), ArloRequestStatusButton(runtime, serial)])
    async_add_entities(entities)


class ArloRefreshButton(ArloEntity, ButtonEntity):
    _attr_name = "Refresh cached status"
    _attr_icon = "mdi:refresh"

    def __init__(self, runtime: ArloRuntime, serial: str) -> None:
        super().__init__(runtime, serial)
        self._attr_unique_id = f"{serial}_refresh_cached"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()


class ArloRequestStatusButton(ArloEntity, ButtonEntity):
    _attr_name = "Request camera status"
    _attr_icon = "mdi:access-point-refresh"

    def __init__(self, runtime: ArloRuntime, serial: str) -> None:
        super().__init__(runtime, serial)
        self._attr_unique_id = f"{serial}_request_status"

    async def async_press(self) -> None:
        await self.runtime.client.request_status(self.serial)
