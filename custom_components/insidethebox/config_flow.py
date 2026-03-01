from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InsideTheBoxClient, InsideTheBoxApiError, InsideTheBoxAuthError
from .const import API_BASE, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _validate(hass: HomeAssistant, token: str) -> None:
    session = async_get_clientsession(hass)
    client = InsideTheBoxClient(session, token, API_BASE)
    await client.get_devices()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()

            try:
                _LOGGER.debug("Validating token via /devices")
                await _validate(self.hass, token)
            except InsideTheBoxAuthError:
                errors["base"] = "invalid_auth"
            except InsideTheBoxApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating token")
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Inside The Box", data={CONF_TOKEN: token})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )