from __future__ import annotations

import logging
from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import S1ErganiApi, S1ErganiApiError
from .const import (
    CONF_AFM,
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_SERVER,
    CONF_USERNAME,
    DEVICE_ID_PREFIX,
    DOMAIN,
    SERVICE_CHECK_IN,
    SERVICE_CHECK_OUT,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _generate_device_id() -> str:
    """Generate a stable S1 Ergani device ID."""
    return f"{DEVICE_ID_PREFIX}{uuid4()}"


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up the S1 Ergani integration."""

    hass.data.setdefault(DOMAIN, {})

    async def async_check_in(call: ServiceCall) -> None:
        """Perform check-in."""

        entries = hass.config_entries.async_entries(DOMAIN)

        if not entries:
            raise HomeAssistantError(
                "S1 Ergani is not configured."
            )

        entry = entries[0]
        api = hass.data[DOMAIN].get(entry.entry_id)

        if api is None:
            raise HomeAssistantError(
                "S1 Ergani is not loaded."
            )

        _LOGGER.warning(
            "S1 Ergani: CHECK-IN requested"
        )

        try:
            result = await api.check_in()

        except S1ErganiApiError as err:
            _LOGGER.error(
                "S1 Ergani CHECK-IN failed: %s",
                err,
            )
            raise HomeAssistantError(
                f"S1 Ergani check-in failed: {err}"
            ) from err

        hass.data[DOMAIN][
            f"{entry.entry_id}_last_result"
        ] = result

        _LOGGER.warning(
            "S1 Ergani CHECK-IN successful: %s",
            result,
        )

    async def async_check_out(call: ServiceCall) -> None:
        """Perform check-out."""

        entries = hass.config_entries.async_entries(DOMAIN)

        if not entries:
            raise HomeAssistantError(
                "S1 Ergani is not configured."
            )

        entry = entries[0]
        api = hass.data[DOMAIN].get(entry.entry_id)

        if api is None:
            raise HomeAssistantError(
                "S1 Ergani is not loaded."
            )

        _LOGGER.warning(
            "S1 Ergani: CHECK-OUT requested"
        )

        try:
            result = await api.check_out()

        except S1ErganiApiError as err:
            _LOGGER.error(
                "S1 Ergani CHECK-OUT failed: %s",
                err,
            )
            raise HomeAssistantError(
                f"S1 Ergani check-out failed: {err}"
            ) from err

        hass.data[DOMAIN][
            f"{entry.entry_id}_last_result"
        ] = result

        _LOGGER.warning(
            "S1 Ergani CHECK-OUT successful: %s",
            result,
        )

    if not hass.services.has_service(
        DOMAIN,
        SERVICE_CHECK_IN,
    ):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHECK_IN,
            async_check_in,
        )

    if not hass.services.has_service(
        DOMAIN,
        SERVICE_CHECK_OUT,
    ):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CHECK_OUT,
            async_check_out,
        )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up S1 Ergani from a config entry."""

    device_id = entry.data.get(CONF_DEVICE_ID)

    if not device_id:
        device_id = _generate_device_id()

        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_DEVICE_ID: device_id,
            },
        )

        _LOGGER.info(
            "S1 Ergani: generated new DEVICEID %s",
            device_id,
        )

    session = async_get_clientsession(hass)

    api = S1ErganiApi(
        session=session,
        server=entry.data[CONF_SERVER],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        afm=entry.data[CONF_AFM],
        device_id=device_id,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = api

    _LOGGER.info(
        "S1 Ergani integration loaded for server %s",
        entry.data[CONF_SERVER],
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload S1 Ergani config entry."""

    hass.data[DOMAIN].pop(
        entry.entry_id,
        None,
    )

    hass.data[DOMAIN].pop(
        f"{entry.entry_id}_last_result",
        None,
    )

    return True