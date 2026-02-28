from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InsideTheBoxClient, InsideTheBoxApiError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class InsideTheBoxCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: InsideTheBoxClient, scan_interval_s: int = DEFAULT_SCAN_INTERVAL) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_s),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.get_devices()
        except InsideTheBoxApiError as e:
            raise UpdateFailed(str(e)) from e