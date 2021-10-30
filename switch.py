from __future__ import annotations

import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


async def async_setup_platform(hass: HomeAssistant, config: ConfigType,
                               async_add_entities: AddEntitiesCallback,
                               discovery_info: DiscoveryInfoType = None) -> None:

    if not discovery_info:
        return

    coils = []
    for port in hass.data[DOMAIN]:
        for device in port.devices:
            coils.extend(device.coils.values())

    if len(coils) > 0:
        async_add_entities(coils)
        _LOGGER.info(f"Coil switches added: {coils}")
