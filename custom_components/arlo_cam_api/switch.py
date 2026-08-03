"""Switch controls for Arlo cameras and Frigate activation."""

from __future__ import annotations

from typing import Awaitable, Callable

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ArloRuntime
from .entity import ArloEntity

CommandFn = Callable[[bool], Awaitable[bool]]
StateFn = Callable[[dict], bool]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: ArloRuntime = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []

    for serial in (runtime.coordinator.data or {}):
        entities.extend(
            [
                ArloCommandSwitch(
                    runtime,
                    serial,
                    "motion_armed",
                    "Motion armed",
                    lambda enabled, serial=serial: runtime.client.arm(serial, enabled),
                    lambda status: str(status.get("PIRTargetState", "")).lower() == "armed",
                    "mdi:motion-sensor",
                ),
                ArloCommandSwitch(
                    runtime,
                    serial,
                    "pir_led",
                    "PIR indicator LED",
                    lambda enabled, serial=serial: runtime.client.set_pir_led(serial, enabled),
                    lambda status: bool(status.get("PIREnableLED", False)),
                    "mdi:led-on",
                ),
                ArloCommandSwitch(
                    runtime,
                    serial,
                    "microphone",
                    "Microphone",
                    lambda enabled, serial=serial: runtime.client.set_microphone(serial, enabled),
                    lambda status: bool(status.get("AudioMicEnable", False)),
                    "mdi:microphone",
                ),
                ArloCommandSwitch(
                    runtime,
                    serial,
                    "speaker",
                    "Speaker enabled",
                    lambda enabled, serial=serial: runtime.client.set_speaker(serial, enabled),
                    lambda status: bool(status.get("AudioSpkrEnable", False)),
                    "mdi:speaker",
                ),
                ArloCommandSwitch(
                    runtime,
                    serial,
                    "motion_spotlight",
                    "Motion spotlight",
                    lambda enabled, serial=serial: runtime.client.register_set(
                        serial,
                        {
                            "NightModeLightSourceAlert": 1 if enabled else 0,
                            "NightVisionMode": True,
                            "PIRAction": "Stream+Spotlight" if enabled else "Stream",
                        },
                    ),
                    lambda status: bool(
                        status.get(
                            "NightModeLightSourceAlert",
                            "Spotlight" in str(status.get("PIRAction", "")),
                        )
                    ),
                    "mdi:spotlight-beam",
                ),
                ArloCommandSwitch(
                    runtime,
                    serial,
                    "night_vision",
                    "Infrared night vision",
                    lambda enabled, serial=serial: runtime.client.register_set(
                        serial, {"NightVisionMode": enabled}
                    ),
                    lambda status: bool(status.get("NightVisionMode", True)),
                    "mdi:weather-night",
                ),
                FrigateSwitch(runtime, serial),
            ]
        )

    async_add_entities(entities)


class ArloCommandSwitch(ArloEntity, SwitchEntity):
    """Optimistic camera setting backed by a verified API command."""

    def __init__(
        self,
        runtime: ArloRuntime,
        serial: str,
        key: str,
        name: str,
        command: CommandFn,
        state: StateFn,
        icon: str,
    ) -> None:
        super().__init__(runtime, serial)
        self._attr_unique_id = f"{serial}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        self._command = command
        self._state = state
        self._optimistic: bool | None = None

    @property
    def is_on(self) -> bool:
        return self._optimistic if self._optimistic is not None else self._state(self.status)

    async def async_turn_on(self, **kwargs) -> None:
        if await self._command(True):
            self._optimistic = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        if await self._command(False):
            self._optimistic = False
            self.async_write_ha_state()


class FrigateSwitch(ArloEntity, SwitchEntity):
    """Control the matching Frigate camera through MQTT."""

    _attr_name = "Frigate camera enabled"
    _attr_icon = "mdi:cctv"

    def __init__(self, runtime: ArloRuntime, serial: str) -> None:
        super().__init__(runtime, serial)
        self._attr_unique_id = f"{serial}_frigate_enabled"

    @property
    def is_on(self) -> bool:
        return self.runtime.frigate_active.get(self.serial, False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.runtime.set_frigate(self.serial, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.runtime.set_frigate(self.serial, False)
        self.async_write_ha_state()
