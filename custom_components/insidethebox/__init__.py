from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlparse

from homeassistant.components.webhook import (
    async_generate_id as webhook_generate_id,
    async_generate_url as webhook_generate_url,
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import InsideTheBoxClient
from .const import (
    API_BASE,
    CONF_TOKEN,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_SECRET,
    DEFAULT_OPEN_DURATION,
    DOMAIN,
    WEBHOOK_EVENT_NAME,
    WEBHOOK_HEADER_NAME,
)
from .coordinator import InsideTheBoxCoordinator

PLATFORMS = ["lock", "sensor"]


def _parse_for_itb(webhook_url: str) -> dict[str, Any]:
    """
    Convert full webhook URL to ITB fields:
      endpointHost, endpointPort, endpointPath, endpointQuerystring, useHttps
    """
    u = urlparse(webhook_url)
    use_https = (u.scheme == "https")
    port = u.port or (443 if use_https else 80)
    host = u.hostname
    if not host:
        raise ValueError("Webhook URL missing hostname")
    return {
        "endpointHost": host,
        "endpointPort": int(port),
        "endpointPath": u.path,
        "endpointQuerystring": (u.query or ""),
        "useHttps": bool(use_https),
    }


async def _ensure_webhook_ids(hass: HomeAssistant, entry: ConfigEntry) -> tuple[str, str]:
    data = dict(entry.data)
    changed = False

    if CONF_WEBHOOK_ID not in data:
        data[CONF_WEBHOOK_ID] = webhook_generate_id()
        changed = True

    if CONF_WEBHOOK_SECRET not in data:
        data[CONF_WEBHOOK_SECRET] = secrets.token_urlsafe(32)
        changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=data)

    return data[CONF_WEBHOOK_ID], data[CONF_WEBHOOK_SECRET]


def _make_webhook_handler(hass: HomeAssistant, entry_id: str):
    async def _handler(hass: HomeAssistant, webhook_id: str, request):
        # Validate shared secret header
        secret_expected = hass.data[DOMAIN][entry_id]["webhook_secret"]
        got = request.headers.get(WEBHOOK_HEADER_NAME, "")
        if not got or got != secret_expected:
            return {"status": 401, "body": "unauthorized"}

        payload = await request.json()

        # Fire HA event for automations
        hass.bus.async_fire(WEBHOOK_EVENT_NAME, payload)

        # Update coordinator data opportunistically (push state)
        coordinator: InsideTheBoxCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        lock_obj = (
            payload.get("deliveryLock")
            or payload.get("lock")
            or payload.get("webhookDevice")
            or None
        )

        if isinstance(lock_obj, dict) and lock_obj.get("lockid"):
            data = coordinator.data or {}
            locks = list(data.get("locks", []))
            updated = False
            for i, obj in enumerate(locks):
                if obj.get("lockid") == lock_obj["lockid"]:
                    locks[i] = {**obj, **lock_obj}
                    updated = True
                    break
            if not updated:
                locks.append(lock_obj)

            coordinator.async_set_updated_data({**data, "locks": locks})

        return {"status": 200}

    return _handler


async def _register_itb_webhooks_for_all_locks(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, str]:
    """Register ITB webhooks per lock. Returns mapping lockid -> webhookid (remote)."""
    ctx = hass.data[DOMAIN][entry.entry_id]
    client: InsideTheBoxClient = ctx["client"]
    coordinator: InsideTheBoxCoordinator = ctx["coordinator"]
    secret: str = ctx["webhook_secret"]
    webhook_id: str = ctx["webhook_id"]

    # Dynamic URL based on HA external URL config
    full_url = webhook_generate_url(hass, webhook_id)
    itb_target = _parse_for_itb(full_url)

    locks = (coordinator.data or {}).get("locks", [])
    remote_map: dict[str, str] = {}

    for lock in locks:
        lockid = lock.get("lockid")
        if not lockid:
            continue

        # Register (201 may not return id; list afterwards and match)
        await client.register_webhook_for_lock(
            lockid,
            endpoint_host=itb_target["endpointHost"],
            endpoint_port=itb_target["endpointPort"],
            endpoint_path=itb_target["endpointPath"],
            endpoint_querystring=itb_target["endpointQuerystring"],
            use_https=itb_target["useHttps"],
            custom_headers={WEBHOOK_HEADER_NAME: secret},
            trigger_webhook=False,
        )

        hooks = await client.list_webhooks_for_lock(lockid)
        for h in hooks:
            if (
                h.get("endpointHost") == itb_target["endpointHost"]
                and int(h.get("endpointPort", 0)) == int(itb_target["endpointPort"])
                and h.get("endpointPath") == itb_target["endpointPath"]
                and (h.get("endpointQuerystring") or "") == (itb_target["endpointQuerystring"] or "")
                and bool(h.get("useHttps")) == bool(itb_target["useHttps"])
                and (h.get("customHeaders") or {}).get(WEBHOOK_HEADER_NAME) == secret
            ):
                if h.get("webhookid"):
                    remote_map[lockid] = h["webhookid"]
                break

    return remote_map


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    token = entry.data[CONF_TOKEN]
    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)
    client = InsideTheBoxClient(session, token, API_BASE)

    coordinator = InsideTheBoxCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    webhook_id, webhook_secret = await _ensure_webhook_ids(hass, entry)

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "default_open_duration": DEFAULT_OPEN_DURATION,
        "webhook_id": webhook_id,
        "webhook_secret": webhook_secret,
        "remote_webhooks": {},  # lockid -> webhookid
    }

    # Register HA webhook handler
    webhook_register(
        hass,
        DOMAIN,
        "Inside The Box",
        webhook_id,
        _make_webhook_handler(hass, entry.entry_id),
        allowed_methods=["POST"],
    )

    # Register ITB webhooks for each lock
    # If HA external URL is not configured, webhook_generate_url may be wrong.
    # In that case polling still works; webhook setup may raise.
    try:
        remote_map = await _register_itb_webhooks_for_all_locks(hass, entry)
        hass.data[DOMAIN][entry.entry_id]["remote_webhooks"] = remote_map
    except Exception:
        # Keep integration running with polling fallback
        pass

    # Services
    async def _svc_reregister(call):
        # Remove remote hooks we know about
        remote = hass.data[DOMAIN][entry.entry_id].get("remote_webhooks", {})
        for webhookid in list(remote.values()):
            if webhookid:
                try:
                    await client.delete_webhook(webhookid, trigger_webhook=False)
                except Exception:
                    pass

        # Refresh device list, then register again
        await coordinator.async_request_refresh()
        remote_map2 = await _register_itb_webhooks_for_all_locks(hass, entry)
        hass.data[DOMAIN][entry.entry_id]["remote_webhooks"] = remote_map2

    hass.services.async_register(DOMAIN, "reregister_webhooks", _svc_reregister)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].get(entry.entry_id, {})
    client: InsideTheBoxClient | None = data.get("client")
    remote_map: dict[str, str] = data.get("remote_webhooks", {})

    # Remove ITB webhooks
    if client and remote_map:
        for webhookid in remote_map.values():
            if webhookid:
                try:
                    await client.delete_webhook(webhookid, trigger_webhook=False)
                except Exception:
                    pass

    # Unregister HA webhook
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id:
        webhook_unregister(hass, webhook_id)

    # Unregister service
    if hass.services.has_service(DOMAIN, "reregister_webhooks"):
        hass.services.async_remove(DOMAIN, "reregister_webhooks")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok