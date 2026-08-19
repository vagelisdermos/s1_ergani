from __future__ import annotations

import logging
from uuid import uuid4

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import S1ErganiApi, S1ErganiApiError
from .const import (
    CONF_AFM,
    CONF_DEVICE_ID,
    CONF_SERVER,
    CONF_USERNAME,
    DEVICE_ID_PREFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _generate_device_id() -> str:
    """Generate a unique device ID."""
    return f"{DEVICE_ID_PREFIX}{uuid4()}"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for S1 Ergani."""

    VERSION = 1

    @staticmethod
    def _normalize_server(server: str) -> str:
        """Normalize the SoftOne server name."""

        server = server.strip()

        if server.startswith("https://"):
            server = server[8:]

        if server.startswith("http://"):
            server = server[7:]

        return server.removesuffix(".oncloud.gr")

    async def _validate_connection(
        self,
        user_input: dict,
    ) -> None:
        """Validate login and authentication."""

        session = async_get_clientsession(self.hass)

        api = S1ErganiApi(
            session=session,
            server=user_input[CONF_SERVER],
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            afm=user_input[CONF_AFM],
            device_id=user_input[CONF_DEVICE_ID],
        )

        login_data = await api.login()
        await api.authenticate(login_data)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ):
        """Handle the initial setup."""

        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_SERVER] = self._normalize_server(
                user_input[CONF_SERVER]
            )

            try:
                await self.async_set_unique_id(
                    user_input[CONF_SERVER].lower()
                )
                self._abort_if_unique_id_configured()

                await self._validate_connection(
                    user_input
                )

            except S1ErganiApiError as err:
                _LOGGER.error(
                    "S1 Ergani connection failed: %s",
                    err,
                )
                errors["base"] = "cannot_connect"

            except Exception as err:
                _LOGGER.exception(
                    "S1 Ergani unexpected error: %s",
                    err,
                )
                errors["base"] = "unknown"

            else:
                return self.async_create_entry(
                    title=(
                        f"S1 Ergani "
                        f"({user_input[CONF_SERVER]})"
                    ),
                    data=user_input,
                )

        device_id = (
            user_input.get(CONF_DEVICE_ID)
            if user_input
            else None
        )

        if not device_id:
            device_id = _generate_device_id()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVER
                    ): str,
                    vol.Required(
                        CONF_USERNAME
                    ): str,
                    vol.Required(
                        CONF_PASSWORD
                    ): vol.All(
                        str,
                        vol.Length(min=1),
                    ),
                    vol.Required(
                        CONF_AFM
                    ): str,
                    vol.Required(
                        CONF_DEVICE_ID,
                        default=device_id,
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ):
        """Handle reconfiguration."""

        errors: dict[str, str] = {}

        entry = self._get_reconfigure_entry()
        current_data = entry.data

        # First time opening Reconfigure:
        # show the form with the existing values.
        if user_input is None:
            device_id = current_data.get(
                CONF_DEVICE_ID
            )

            if not device_id:
                device_id = _generate_device_id()

            return self.async_show_form(
                step_id="reconfigure",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_SERVER,
                            default=current_data.get(
                                CONF_SERVER,
                                "",
                            ),
                        ): str,
                        vol.Required(
                            CONF_USERNAME,
                            default=current_data.get(
                                CONF_USERNAME,
                                "",
                            ),
                        ): str,
                        vol.Required(
                            CONF_PASSWORD,
                            default=current_data.get(
                                CONF_PASSWORD,
                                "",
                            ),
                        ): vol.All(
                            str,
                            vol.Length(min=1),
                        ),
                        vol.Required(
                            CONF_AFM,
                            default=current_data.get(
                                CONF_AFM,
                                "",
                            ),
                        ): str,
                        vol.Required(
                            CONF_DEVICE_ID,
                            default=device_id,
                        ): str,
                    }
                ),
                errors=errors,
            )

        # User has submitted the form.
        user_input[CONF_SERVER] = self._normalize_server(
            user_input[CONF_SERVER]
        )

        try:
            await self.async_set_unique_id(
                entry.unique_id or ""
            )
            self._abort_if_unique_id_mismatch()

            await self._validate_connection(
                user_input
            )

        except S1ErganiApiError as err:
            _LOGGER.error(
                "S1 Ergani reconfiguration failed: %s",
                err,
            )
            errors["base"] = "cannot_connect"

        except Exception as err:
            _LOGGER.exception(
                "S1 Ergani unexpected reconfiguration error: %s",
                err,
            )
            errors["base"] = "unknown"

        else:
            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVER,
                        default=user_input.get(
                            CONF_SERVER,
                            "",
                        ),
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=user_input.get(
                            CONF_USERNAME,
                            "",
                        ),
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=user_input.get(
                            CONF_PASSWORD,
                            "",
                        ),
                    ): vol.All(
                        str,
                        vol.Length(min=1),
                    ),
                    vol.Required(
                        CONF_AFM,
                        default=user_input.get(
                            CONF_AFM,
                            "",
                        ),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_ID,
                        default=user_input.get(
                            CONF_DEVICE_ID,
                            _generate_device_id(),
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )