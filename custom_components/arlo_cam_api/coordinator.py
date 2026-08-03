"""Coordinator and runtime orchestration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import logging
from typing import Any

from homeassistant.components.mqtt import async_publish
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

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
                status, registration = await asyncio.gather(
                    self.client.get_status(serial),
                    self.client.get_registration(serial),
                )
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
        mapped = self.camera_map().get(serial)
        if mapped:
            return slugify(mapped)
        camera = (self.coordinator.data or {}).get(serial, {})
        device = camera.get("device", {})
        friendly = device.get("friendly_name") or device.get("hostname") or serial
        return slugify(str(friendly))

    async def set_frigate(self, serial: str, enabled: bool) -> None:
        camera = self.camera_name(serial)
        topic = f"{self.mqtt_prefix}/{camera}/enabled/set"
        await async_publish(self.hass, topic, "ON" if enabled else "OFF", qos=1, retain=False)
        self.frigate_active[serial] = enabled

    async def motion_started(self, serial: str) -> None:
        await self.set_frigate(serial, True)
        self._replace_timer(serial, int(self.entry.options.get(CONF_MAX_ACTIVE, DEFAULT_MAX_ACTIVE)))

    async def motion_stopped(self, serial: str) -> None:
        self._replace_timer(serial, int(self.entry.options.get(CONF_MOTION_TAIL, DEFAULT_MOTION_TAIL)))

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
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
