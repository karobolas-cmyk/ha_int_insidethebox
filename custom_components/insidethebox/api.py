from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp


class InsideTheBoxApiError(Exception):
    """Generic API error."""


class InsideTheBoxAuthError(InsideTheBoxApiError):
    """Auth error (401/403/452)."""


@dataclass
class InsideTheBoxClient:
    session: aiohttp.ClientSession
    token: str
    base_url: str = "https://api.insidethebox.se/iotapi"

    def _headers(self) -> dict[str, str]:
        # Docs: Authorization: Token <API token>
        return {"Authorization": f"Token {self.token}"}

    async def _request(self, method: str, path: str, *, params: Optional[dict[str, Any]] = None, json_body: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            async with self.session.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json_body,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403, 452):
                    text = await resp.text()
                    raise InsideTheBoxAuthError(f"Auth error {resp.status}: {text}")

                if resp.status >= 400:
                    text = await resp.text()
                    raise InsideTheBoxApiError(f"HTTP {resp.status}: {text}")

                # Some endpoints return JSON, others may return empty body/text
                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()

        except asyncio.TimeoutError as e:
            raise InsideTheBoxApiError("Timeout calling Inside The Box API") from e
        except aiohttp.ClientError as e:
            raise InsideTheBoxApiError(f"Network error: {e}") from e

    async def get_devices(self) -> dict[str, Any]:
        # GET /iotapi/devices
        data = await self._request("GET", "/devices")
        return data if isinstance(data, dict) else {}

    async def open_lock(self, lockid: str, open_duration_seconds: int | None = None) -> None:
        # GET /iotapi/lock/open/{lockid}?openDurationSeconds=0..25
        params = {}
        if open_duration_seconds is not None:
            params["openDurationSeconds"] = int(open_duration_seconds)
        await self._request("GET", f"/lock/open/{lockid}", params=params or None)

    async def close_lock(self, lockid: str) -> None:
        # GET /iotapi/lock/close/{lockid}
        await self._request("GET", f"/lock/close/{lockid}")

    async def register_webhook_for_lock(
        self,
        lockid: str,
        *,
        endpoint_host: str,
        endpoint_port: int,
        endpoint_path: str,
        endpoint_querystring: str = "",
        use_https: bool = True,
        custom_headers: dict[str, str] | None = None,
        trigger_webhook: bool = False,
    ) -> None:
        # POST /iotapi/webhook/lock/{lockid}?triggerWebhook=false
        params = {"triggerWebhook": "true" if trigger_webhook else "false"}
        body: dict[str, Any] = {
            "endpointHost": endpoint_host,
            "endpointPort": int(endpoint_port),
            "endpointPath": endpoint_path,
            "endpointQuerystring": endpoint_querystring or "",
            "useHttps": bool(use_https),
        }
        if custom_headers:
            body["customHeaders"] = custom_headers

        await self._request("POST", f"/webhook/lock/{lockid}", params=params, json_body=body)

    async def list_webhooks_for_lock(self, lockid: str) -> list[dict[str, Any]]:
        # GET /iotapi/webhook/lock/{lockid}
        data = await self._request("GET", f"/webhook/lock/{lockid}")
        return data if isinstance(data, list) else []

    async def delete_webhook(self, webhookid: str, *, trigger_webhook: bool = False) -> None:
        # DELETE /iotapi/webhook/{webhookid}?triggerWebhook=false
        params = {"triggerWebhook": "true" if trigger_webhook else "false"}
        await self._request("DELETE", f"/webhook/{webhookid}", params=params)