from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InsideTheBoxCoordinator


@dataclass(frozen=True, kw_only=True)
class ITBSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


LOCK_SENSORS: list[ITBSensorEntityDescription] = [
    ITBSensorEntityDescription(
        key="lockBatteryLevel",
        name="Battery level",
        icon="mdi:battery",
        value_fn=lambda o: o.get("lockBatteryLevel"),
    ),
    ITBSensorEntityDescription(
        key="lockAccessibilityState",
        name="Accessibility",
        icon="mdi:shield-lock",
        value_fn=lambda o: o.get("lockAccessibilityState"),
    ),
]

GATEWAY_SENSORS: list[ITBSensorEntityDescription] = [
    ITBSensorEntityDescription(
        key="gatewayConnectionStatus",
        name="Connection",
        icon="mdi:lan-connect",
        value_fn=lambda o: o.get("gatewayConnectionStatus"),
    ),
    ITBSensorEntityDescription(
        key="gatewayConnectionChangedTimestamp",
        name="Connection changed",
        icon="mdi:clock-outline",
        value_fn=lambda o: o.get("gatewayConnectionChangedTimestamp"),
    ),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    ctx = hass.data[DOMAIN][entry.entry_id]
    coordinator: InsideTheBoxCoordinator = ctx["coordinator"]

    entities: list[SensorEntity] = []

    for lock_obj in (coordinator.data or {}).get("locks", []):
        lockid = lock_obj.get("lockid")
        name = lock_obj.get("name") or lock_obj.get("description") or lockid
        for desc in LOCK_SENSORS:
            entities.append(InsideTheBoxLockSensor(coordinator, lockid, name, desc))

    for gw_obj in (coordinator.data or {}).get("gateways", []):
        gid = gw_obj.get("gatewayid")
        name = gw_obj.get("name") or gw_obj.get("description") or gid
        for desc in GATEWAY_SENSORS:
            entities.append(InsideTheBoxGatewaySensor(coordinator, gid, name, desc))

    async_add_entities(entities)


class _Base(CoordinatorEntity[InsideTheBoxCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: InsideTheBoxCoordinator, device_id: str, device_name: str, desc: ITBSensorEntityDescription):
        super().__init__(coordinator)
        self.entity_description = desc
        self._device_id = device_id
        self._device_name = device_name

    @property
    def native_value(self):
        obj = self._find_obj() or {}
        return self.entity_description.value_fn(obj)


class InsideTheBoxLockSensor(_Base):
    def __init__(self, coordinator, lockid: str, lock_name: str, desc: ITBSensorEntityDescription):
        super().__init__(coordinator, lockid, lock_name, desc)
        self._attr_unique_id = f"insidethebox_lock_{lockid}_{desc.key}"
        self._attr_name = desc.name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, lockid)},
            "name": lock_name,
            "manufacturer": "Inside The Box",
            "model": "LOCK",
        }

    def _find_obj(self) -> dict[str, Any] | None:
        for o in (self.coordinator.data or {}).get("locks", []):
            if o.get("lockid") == self._device_id:
                return o
        return None


class InsideTheBoxGatewaySensor(_Base):
    def __init__(self, coordinator, gatewayid: str, gw_name: str, desc: ITBSensorEntityDescription):
        super().__init__(coordinator, gatewayid, gw_name, desc)
        self._attr_unique_id = f"insidethebox_gateway_{gatewayid}_{desc.key}"
        self._attr_name = desc.name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, gatewayid)},
            "name": gw_name,
            "manufacturer": "Inside The Box",
            "model": "GATEWAY",
        }

    def _find_obj(self) -> dict[str, Any] | None:
        for o in (self.coordinator.data or {}).get("gateways", []):
            if o.get("gatewayid") == self._device_id:
                return o
        return None