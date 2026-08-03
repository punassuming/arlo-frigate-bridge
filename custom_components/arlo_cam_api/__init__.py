"""Arlo Cam API integration."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ArloCamApiClient
from .const import CONF_BASE_URL, DOMAIN, PLATFORMS, WEBHOOK_KINDS
from .coordinator import ArloCoordinator, ArloRuntime


def webhook_id(entry_id: str, kind: str) -> str:
    return f"{DOMAIN}_{entry_id}_{kind}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = ArloCamApiClient(async_get_clientsession(hass), entry.data[CONF_BASE_URL])
    coordinator = ArloCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    runtime = ArloRuntime(hass, entry, client, coordinator)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    async def handle(kind: str, request: web.Request) -> web.Response:
        payload = await request.json()
        serial = str(payload.get("serial_number", ""))
        if kind == "motion" and serial:
            await runtime.motion_started(serial)
        elif kind == "motion_timeout" and serial:
            await runtime.motion_stopped(serial)
        elif kind == "status" and serial:
            status = payload.get("status")
            if isinstance(status, dict):
                coordinator.merge_status(serial, status)
        elif kind == "registration":
            await coordinator.async_request_refresh()
        return web.Response(status=200)

    for kind in WEBHOOK_KINDS:
        webhook.async_register(
            hass,
            DOMAIN,
            f"Arlo Cam API {kind}",
            webhook_id(entry.entry_id, kind),
            lambda _hass, _webhook_id, request, kind=kind: handle(kind, request),
            local_only=False,
        )

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime: ArloRuntime = hass.data[DOMAIN].pop(entry.entry_id)
        await runtime.shutdown()
        for kind in WEBHOOK_KINDS:
            webhook.async_unregister(hass, webhook_id(entry.entry_id, kind))
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
