"""Sensors for Arlo Cam API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import webhook_id
from .const import DOMAIN, WEBHOOK_KINDS
from .coordinator import ArloRuntime
from .entity import ArloEntity, ArloServerEntity


@dataclass(frozen=True, kw_only=True)
class ArloSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


SENSORS = (
    ArloSensorDescription(key="battery", name="Battery", native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.get("BatPercent")),
    ArloSensorDescription(key="battery_voltage", name="Battery voltage", native_unit_of_measurement=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=3, value_fn=lambda s: s.get("Bat1Volt")),
    ArloSensorDescription(key="temperature", name="Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.get("Temperature")),
    ArloSensorDescription(key="wifi_rssi", name="Wi-Fi RSSI", native_unit_of_measurement="dBm", device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.get("WifiRSSI")),
    ArloSensorDescription(key="signal", name="Signal indicator", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.get("SignalStrengthIndicator")),
    ArloSensorDescription(key="failed_streams", name="Failed streams", state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda s: s.get("FailedStreams")),
    ArloSensorDescription(key="firmware", name="Firmware", entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.get("SystemFirmwareVersion")),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime: ArloRuntime = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        ArloSensor(runtime, serial, description)
        for serial in (runtime.coordinator.data or {})
        for description in SENSORS
    ]
    entities.append(ArloWebhookSensor(runtime))
    async_add_entities(entities)


class ArloSensor(ArloEntity, SensorEntity):
    entity_description: ArloSensorDescription

    def __init__(self, runtime: ArloRuntime, serial: str, description: ArloSensorDescription) -> None:
        super().__init__(runtime, serial)
        self.entity_description = description
        self._attr_unique_id = f"{serial}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.status)


class ArloWebhookSensor(ArloServerEntity, SensorEntity):
    _attr_name = "Webhook paths"
    _attr_icon = "mdi:webhook"
    _attr_entity_category = "diagnostic"

    def __init__(self, runtime: ArloRuntime) -> None:
        super().__init__(runtime)
        self._attr_unique_id = f"{runtime.entry.entry_id}_webhook_paths"

    @property
    def native_value(self) -> str:
        return "configured"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"entry_id": self.runtime.entry.entry_id, **{
            kind: f"/api/webhook/{webhook_id(self.runtime.entry.entry_id, kind)}"
            for kind in WEBHOOK_KINDS
        }}
