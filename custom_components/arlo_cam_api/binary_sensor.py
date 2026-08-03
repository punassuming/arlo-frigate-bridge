"""Binary sensors for Arlo Cam API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ArloRuntime
from .entity import ArloEntity


@dataclass(frozen=True, kw_only=True)
class ArloBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSORS = (
    ArloBinaryDescription(key="charging", name="Charging", device_class=BinarySensorDeviceClass.BATTERY_CHARGING, value_fn=lambda s: str(s.get("ChargingState", "Off")).lower() == "on"),
    ArloBinaryDescription(key="critical_battery", name="Critical battery", device_class=BinarySensorDeviceClass.PROBLEM, value_fn=lambda s: bool(int(s.get("CriticalBatStatus", 0) or 0))),
    ArloBinaryDescription(key="ir_leds", name="Infrared LEDs active", icon="mdi:weather-night", value_fn=lambda s: bool(int(s.get("IRLEDsOn", 0) or 0))),
    ArloBinaryDescription(key="spotlight", name="Spotlight reported enabled", icon="mdi:spotlight-beam", value_fn=lambda s: bool(s.get("SpotlightEnabled", False))),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime: ArloRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ArloBinarySensor(runtime, serial, description)
        for serial in (runtime.coordinator.data or {})
        for description in BINARY_SENSORS
    )


class ArloBinarySensor(ArloEntity, BinarySensorEntity):
    entity_description: ArloBinaryDescription

    def __init__(self, runtime: ArloRuntime, serial: str, description: ArloBinaryDescription) -> None:
        super().__init__(runtime, serial)
        self.entity_description = description
        self._attr_unique_id = f"{serial}_{description.key}"

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.status)
