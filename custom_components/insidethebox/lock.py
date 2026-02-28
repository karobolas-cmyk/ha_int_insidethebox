from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InsideTheBoxCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    ctx = hass.data[DOMAIN][entry.entry_id]
    coordinator: InsideTheBoxCoordinator = ctx["coordinator"]
    default_open_duration: int = ctx["default_open_duration"]

    locks = (coordinator.data or {}).get("locks", [])
    async_add_entities([InsideTheBoxLock(coordinator, obj, default_open_duration) for obj in locks])


class InsideTheBoxLock(CoordinatorEntity[InsideTheBoxCoordinator], LockEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: InsideTheBoxCoordinator, lock_obj: dict[str, Any], default_open_duration: int) -> None:
        super().__init__(coordinator)
        self._lockid = lock_obj.get("lockid")
        self._name = lock_obj.get("name") or lock_obj.get("description") or self._lockid
        self._default_open_duration = default_open_duration

        self._attr_unique_id = f"insidethebox_lock_{self._lockid}"
        self._attr_name = self._name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._lockid)},
            "name": self._name,
            "manufacturer": "Inside The Box",
            "model": "LOCK",
        }

    def _find_self(self) -> dict[str, Any] | None:
        for o in (self.coordinator.data or {}).get("locks", []):
            if o.get("lockid") == self._lockid:
                return o
        return None

    @property
    def is_locked(self) -> bool | None:
        obj = self._find_self()
        if not obj:
            return None
        is_open = obj.get("isLockOpen")
        if is_open is None:
            return None
        return not bool(is_open)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        obj = self._find_self() or {}
        return {
            "lockid": self._lockid,
            "state": obj.get("state"),
            "lockAccessibilityState": obj.get("lockAccessibilityState"),
            "lastLockOpenOrCloseTimestamp": obj.get("lastLockOpenOrCloseTimestamp"),
        }

    async def async_unlock(self, **kwargs: Any) -> None:
        duration = kwargs.get("open_duration_seconds", self._default_open_duration)
        if duration is not None:
            duration = max(0, min(25, int(duration)))

        await self.coordinator.client.open_lock(self._lockid, open_duration_seconds=duration)
        await self.coordinator.async_request_refresh()

    async def async_lock(self, **kwargs: Any) -> None:
        await self.coordinator.client.close_lock(self._lockid)
        await self.coordinator.async_request_refresh()