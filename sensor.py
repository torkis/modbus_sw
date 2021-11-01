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

    inputs = []
    for port in hass.data[DOMAIN]:
        for device in port.devices:
            inputs.extend(device.inputs.values())

    if len(inputs) > 0:
        async_add_entities(inputs)
        _LOGGER.info(f"Input sensors added: {inputs}")
