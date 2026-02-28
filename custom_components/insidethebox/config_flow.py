from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import InsideTheBoxClient, InsideTheBoxApiError, InsideTheBoxAuthError
from .const import API_BASE, CONF_TOKEN, DOMAIN


async def _validate(hass: HomeAssistant, token: str) -> None:
    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)
    client = InsideTheBoxClient(session, token, API_BASE)
    await client.get_devices()


class InsideTheBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()

            try:
                await _validate(self.hass, token)
            except InsideTheBoxAuthError:
                errors["base"] = "invalid_auth"
            except InsideTheBoxApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="Inside The Box",
                    data={CONF_TOKEN: token},
                )

        schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)