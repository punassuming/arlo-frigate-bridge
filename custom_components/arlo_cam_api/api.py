"""HTTP client for brianschrameck/arlo-cam-api."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession


class ArloCamApiError(Exception):
    """Base API error."""


class ArloCamApiClient:
    """Small async client around the local REST API."""

    def __init__(self, session: ClientSession, base_url: str) -> None:
        self._session = session
        self.base_url = base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            async with self._session.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                timeout=10,
            ) as response:
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
        except (ClientError, ClientResponseError, TimeoutError) as err:
            raise ArloCamApiError(str(err)) from err

    async def list_devices(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/device")
        return data if isinstance(data, list) else []

    async def get_status(self, serial: str) -> dict[str, Any]:
        data = await self._request("GET", f"/device/{serial}")
        return data if isinstance(data, dict) else {}

    async def get_registration(self, serial: str) -> dict[str, Any]:
        data = await self._request("GET", f"/device/{serial}/registration")
        return data if isinstance(data, dict) else {}

    async def request_status(self, serial: str) -> bool:
        data = await self._request("POST", f"/device/{serial}/statusrequest")
        return bool(data.get("result")) if isinstance(data, dict) else False

    async def arm(self, serial: str, enabled: bool, sensitivity: int = 80) -> bool:
        # Use a minimal registerSet so arming does not overwrite the independent
        # motion-spotlight and night-vision policy.
        return await self.register_set(
            serial,
            {
                "PIRTargetState": "Armed" if enabled else "Disarmed",
                "PIRStartSensitivity": sensitivity,
            },
        )

    async def set_pir_led(self, serial: str, enabled: bool, sensitivity: int = 80) -> bool:
        data = await self._request(
            "POST",
            f"/device/{serial}/pirled",
            json={"enabled": enabled, "sensitivity": sensitivity},
        )
        return bool(data.get("result"))

    async def set_microphone(self, serial: str, enabled: bool) -> bool:
        data = await self._request(
            "POST", f"/device/{serial}/audiomic", json={"enabled": enabled}
        )
        return bool(data.get("result"))

    async def set_speaker(self, serial: str, enabled: bool) -> bool:
        data = await self._request(
            "POST", f"/device/{serial}/audiospeaker", json={"enabled": enabled}
        )
        return bool(data.get("result"))

    async def set_quality(self, serial: str, quality: str) -> bool:
        data = await self._request(
            "POST", f"/device/{serial}/quality", json={"quality": quality}
        )
        return bool(data.get("result"))

    async def register_set(self, serial: str, values: dict[str, Any]) -> bool:
        data = await self._request(
            "POST", f"/device/{serial}/registerset", json=values
        )
        return bool(data.get("result"))
