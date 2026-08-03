"""Shared entity helpers."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import ArloCoordinator, ArloRuntime


class ArloEntity(CoordinatorEntity[ArloCoordinator]):
    """Base class for camera entities."""

    _attr_has_entity_name = True

    def __init__(self, runtime: ArloRuntime, serial: str) -> None:
        super().__init__(runtime.coordinator)
        self.runtime = runtime
        self.serial = serial

    @property
    def camera_data(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get(self.serial, {})

    @property
    def status(self) -> dict[str, Any]:
        return self.camera_data.get("status", {})

    @property
    def registration(self) -> dict[str, Any]:
        return self.camera_data.get("registration", {})

    @property
    def device_info(self) -> DeviceInfo:
        device = self.camera_data.get("device", {})
        model = self.registration.get("SystemModelNumber") or self.status.get("SystemModelNumber")
        return DeviceInfo(
            identifiers={(DOMAIN, self.serial)},
            name=device.get("friendly_name") or device.get("hostname") or f"Arlo {self.serial}",
            manufacturer="Arlo",
            model=model or "Local camera",
            serial_number=self.serial,
            sw_version=self.status.get("SystemFirmwareVersion") or self.registration.get("SystemFirmwareVersion"),
            configuration_url=f"{self.runtime.client.base_url}/device/{self.serial}",
        )


class ArloServerEntity(CoordinatorEntity[ArloCoordinator]):
    """Base class for server-level entities."""

    _attr_has_entity_name = True

    def __init__(self, runtime: ArloRuntime) -> None:
        super().__init__(runtime.coordinator)
        self.runtime = runtime

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.runtime.entry.entry_id)},
            name=NAME,
            manufacturer="Community",
            model="arlo-cam-api server",
            configuration_url=self.runtime.client.base_url,
        )
