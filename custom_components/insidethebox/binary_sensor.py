from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InsideTheBoxCoordinator


ACCESSIBLE_TRUE = {"ACCESSIBLE", "ACCESSIBLE_REMOTELY"}
ACTIVE_TRUE = {"ACTIVE"}


@dataclass(frozen=True, kw_only=True)
class ITBBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]


LOCK_BINARY_SENSORS: list[ITBBinaryDescription] = [
    ITBBinaryDescription(
        key="accessible",
        name="Accessible",
        icon="mdi:shield-check",
        value_fn=lambda o: (o.get("lockAccessibilityState") in ACCESSIBLE_TRUE)
        if o.get("lockAccessibilityState") is not None
        else None,
    ),
    ITBBinaryDescription(
        key="active",
        name="Active",
        icon="mdi:power",
        value_fn=lambda o: (o.get("state") in ACTIVE_TRUE) if o.get("state") is not None else None,
    ),
    ITBBinaryDescription(
        key="open",
        name="Open",
        icon="mdi:door-open",
        value_fn=lambda o: bool(o.get("isLockOpen")) if o.get("isLockOpen") is not None else None,
    ),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    ctx = hass.data[DOMAIN][entry.entry_id]
    coordinator: InsideTheBoxCoordinator = ctx["coordinator"]

    entities: list[BinarySensorEntity] = []
    for lock_obj in (coordinator.data or {}).get("locks", []):
        lockid = lock_obj.get("lockid")
        name = lock_obj.get("name") or lock_obj.get("description") or lockid
        for desc in LOCK_BINARY_SENSORS:
            entities.append(InsideTheBoxLockBinarySensor(coordinator, lockid, name, desc))

    async_add_entities(entities)


class InsideTheBoxLockBinarySensor(CoordinatorEntity[InsideTheBoxCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: InsideTheBoxCoordinator, lockid: str, lock_name: str, desc: ITBBinaryDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = desc
        self._lockid = lockid

        self._attr_unique_id = f"insidethebox_lock_{lockid}_{desc.key}"
        self._attr_name = desc.name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, lockid)},
            "name": lock_name,
            "manufacturer": "Inside The Box",
            "model": "LOCK",
        }

    def _find_lock(self) -> dict[str, Any] | None:
        for o in (self.coordinator.data or {}).get("locks", []):
            if o.get("lockid") == self._lockid:
                return o
        return None

    @property
    def is_on(self) -> bool | None:
        lock = self._find_lock() or {}
        return self.entity_description.value_fn(lock)