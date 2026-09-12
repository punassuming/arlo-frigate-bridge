"""Coordinator and runtime orchestration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import logging
from typing import Any

from homeassistant.components.mqtt import async_publish, async_subscribe
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ArloCamApiClient, ArloCamApiError
from .const import (
    CONF_CAMERA_MAP,
    CONF_MAX_ACTIVE,
    CONF_MOTION_TAIL,
    CONF_MQTT_PREFIX,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_ACTIVE,
    DEFAULT_MOTION_TAIL,
    DEFAULT_MQTT_PREFIX,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ArloCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Poll cached camera metadata and status."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: ArloCamApiClient,
    ) -> None:
        self.entry = entry
        self.client = client
        scan_interval = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.client.list_devices()
            result: dict[str, dict[str, Any]] = {}
            for device in devices:
                serial = str(device.get("serial_number", "")).strip()
                if not serial:
                    continue
                status = await self.client.get_status(serial)
                try:
                    registration = await self.client.get_registration(serial)
                except ArloCamApiError:
                    # Registration metadata is diagnostic only. Some upstream
                    # versions do not provide this endpoint consistently.
                    registration = {}
                result[serial] = {
                    "device": device,
                    "status": status,
                    "registration": registration,
                }
            return result
        except ArloCamApiError as err:
            raise UpdateFailed(f"Unable to reach arlo-cam-api: {err}") from err

    def merge_status(self, serial: str, status: dict[str, Any]) -> None:
        data = dict(self.data or {})
        camera = dict(data.get(serial, {}))
        camera["status"] = status
        data[serial] = camera
        self.async_set_updated_data(data)


class ArloRuntime:
    """Own coordinator, webhook timers, and Frigate MQTT state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: ArloCamApiClient,
        coordinator: ArloCoordinator,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.client = client
        self.coordinator = coordinator
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._unsubscribe_frigate_state = None
        self._unsubscribe_frigate_availability = None
        self._unsubscribe_home_assistant_started = None
        self.frigate_requested: dict[str, bool] = {}
        self.frigate_active: dict[str, bool] = {}

    @property
    def mqtt_prefix(self) -> str:
        return str(self.entry.options.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)).strip("/")

    def camera_map(self) -> dict[str, str]:
        raw = self.entry.options.get(CONF_CAMERA_MAP, "{}")
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
        try:
            parsed = json.loads(str(raw))
            return {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def camera_name(self, serial: str) -> str:
        """Return the explicit Frigate camera mapping, never an inferred topic."""
        return self.camera_map().get(serial, "")

    async def async_start(self) -> None:
        """Subscribe to Frigate's authoritative camera-enabled state."""
        topic = f"{self.mqtt_prefix}/+/enabled/state"
        self._unsubscribe_frigate_state = await async_subscribe(
            self.hass, topic, self._handle_frigate_state
        )
        self._unsubscribe_frigate_availability = await async_subscribe(
            self.hass, f"{self.mqtt_prefix}/available", self._handle_frigate_availability
        )
        if self.hass.is_running:
            await self.async_force_all_off()
        else:
            self._unsubscribe_home_assistant_started = self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self._handle_home_assistant_started
            )

    @property
    def configured_serials(self) -> set[str]:
        """Return cameras eligible to control Frigate through MQTT."""
        return set(self.camera_map())

    @property
    def _camera_to_serial(self) -> dict[str, str]:
        return {camera: serial for serial, camera in self.camera_map().items()}

    def _handle_frigate_state(self, message) -> None:
        """Record an acknowledgement from Frigate, not merely a published command."""
        suffix = "/enabled/state"
        if not message.topic.startswith(f"{self.mqtt_prefix}/") or not message.topic.endswith(suffix):
            return
        camera = message.topic[len(self.mqtt_prefix) + 1 : -len(suffix)]
        serial = self._camera_to_serial.get(camera)
        if serial is None:
            return
        payload = message.payload.strip().upper()
        if payload not in {"ON", "OFF"}:
            _LOGGER.warning("Ignoring unexpected Frigate enabled state for %s: %s", camera, payload)
            return
        self.frigate_active[serial] = payload == "ON"
        self.coordinator.async_update_listeners()

    async def set_frigate(self, serial: str, enabled: bool) -> bool:
        return await self._set_frigate(serial, enabled)

    async def _set_frigate(self, serial: str, enabled: bool, *, retain: bool = False) -> bool:
        camera = self.camera_name(serial)
        if not camera:
            _LOGGER.warning("Ignoring Frigate command for unmapped Arlo serial %s", serial)
            return False
        topic = f"{self.mqtt_prefix}/{camera}/enabled/set"
        await async_publish(self.hass, topic, "ON" if enabled else "OFF", qos=1, retain=retain)
        self.frigate_requested[serial] = enabled
        return True

    async def motion_started(self, serial: str) -> None:
        if serial not in self.configured_serials:
            _LOGGER.warning("Ignoring motion webhook for unmapped Arlo serial %s", serial)
            return
        await self.set_frigate(serial, True)
        self._replace_timer(serial, int(self.entry.options.get(CONF_MAX_ACTIVE, DEFAULT_MAX_ACTIVE)))

    async def motion_stopped(self, serial: str) -> None:
        if serial not in self.configured_serials:
            _LOGGER.warning("Ignoring motion timeout webhook for unmapped Arlo serial %s", serial)
            return
        self._replace_timer(serial, int(self.entry.options.get(CONF_MOTION_TAIL, DEFAULT_MOTION_TAIL)))

    def _handle_home_assistant_started(self, _event: Event) -> None:
        self.hass.async_create_task(self.async_force_all_off())

    def _handle_frigate_availability(self, message) -> None:
        if message.payload.strip().lower() == "online":
            self.hass.async_create_task(self.async_force_all_off())

    async def async_force_all_off(self) -> None:
        """Return every mapped battery camera to its safe disabled state."""
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
        for serial in self.configured_serials:
            await self._set_frigate(serial, False, retain=True)

    def _replace_timer(self, serial: str, delay: int) -> None:
        old = self._tasks.pop(serial, None)
        if old:
            old.cancel()
        self._tasks[serial] = self.hass.async_create_task(self._delayed_off(serial, delay))

    async def _delayed_off(self, serial: str, delay: int) -> None:
        try:
            await asyncio.sleep(max(0, delay))
            await self.set_frigate(serial, False)
        except asyncio.CancelledError:
            return
        finally:
            self._tasks.pop(serial, None)

    async def shutdown(self) -> None:
        if self._unsubscribe_frigate_state is not None:
            self._unsubscribe_frigate_state()
            self._unsubscribe_frigate_state = None
        if self._unsubscribe_frigate_availability is not None:
            self._unsubscribe_frigate_availability()
            self._unsubscribe_frigate_availability = None
        if self._unsubscribe_home_assistant_started is not None:
            self._unsubscribe_home_assistant_started()
            self._unsubscribe_home_assistant_started = None
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
