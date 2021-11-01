"""The Modbus Switch integration."""
from __future__ import annotations

import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_DEVICES,
    CONF_ID,
    CONF_DEVICE_ID,
)

from .const import *
from .device import ModbusPort

_LOGGER = logging.getLogger(__name__)

COIL_SCHEMA_ENTRY = vol.Schema(
    {
        vol.Required(CONF_ID): vol.Range(min=0, max=31),
        vol.Required(CONF_NAME): cv.string
    }
)

DEVICE_SCHEMA_ENTRY = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_SLAVE_ID): vol.Range(min=1, max=247),
        vol.Optional(CONF_COILS): vol.All(
            cv.ensure_list, [COIL_SCHEMA_ENTRY]
        )
    }
)

MODBUS_PORT_SCHEMA_ENTRY = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Optional(CONF_BAUDRATE, default=9600): cv.positive_int,
        vol.Optional(CONF_STOPBITS, default=1): vol.Any(1, 2),
        vol.Optional(CONF_BYTESIZE, default=8): vol.Any(5, 6, 7, 8),
        vol.Optional(CONF_PARITY, default="N"): vol.Any("E", "O", "N"),
        vol.Optional(CONF_RTSMODE, default="U"): vol.Any("U", "D"),
        vol.Required(CONF_RTSPIN): cv.positive_int,
        vol.Optional(CONF_RTSDELAY, default=100): cv.positive_int,
        vol.Optional(CONF_DEVICES): vol.All(
            cv.ensure_list, [DEVICE_SCHEMA_ENTRY]
        )
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(cv.ensure_list, [MODBUS_PORT_SCHEMA_ENTRY])
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:

    if DOMAIN not in config:
        return True

    ports = []
    for port_config in config[DOMAIN]:
        ports.append(ModbusPort(hass, port_config))
    hass.data[DOMAIN] = ports

    await discovery.async_load_platform(hass, "switch", DOMAIN, { DOMAIN: ""}, config)

    for port in ports:
        await port.async_enable_auto_update(timedelta(seconds=30), True)

    return True
