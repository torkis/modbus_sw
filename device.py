from __future__ import annotations

import logging
import asyncio
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.switch import SwitchEntity

from homeassistant.const import (
    CONF_NAME,
    CONF_ID,
    CONF_DEVICES,
    CONF_PORT
)

from .const import *

from .modbus_rs485pi import ModbusRtu

_LOGGER = logging.getLogger(__name__)


class ModbusPort:

    def __init__(self, hass: HomeAssistant, config: ConfigType):
        self.hass = hass
        self.name = config.get(CONF_NAME)

        self.devices = []
        if config.get(CONF_DEVICES):
            for device_config in config.get(CONF_DEVICES):
                self.devices.append(ModbusDevice(self, device_config))

        self._lock = asyncio.Lock()
        self._msg_wait = 0

        self._driver = ModbusRtu(
            config.get(CONF_PORT),
            config.get(CONF_BAUDRATE),
            config.get(CONF_PARITY),
            config.get(CONF_BYTESIZE),
            config.get(CONF_STOPBITS),
            config.get(CONF_RTSMODE),
            config.get(CONF_RTSPIN),
            config.get(CONF_RTSDELAY)
        )
        self._driver.connect()


    def __str__(self):
        return f"<ModbusPort {self.name}>"

    def _read_coil(self, coil: CoilEntity) -> bool:
        self._driver.set_slave(coil.device.slave_id)
        return bool(self._driver.read_bits(coil.id, 1)[0])

    def _write_coil(self, coil: CoilEntity, value: bool):
        self._driver.set_slave(coil.device.slave_id)
        self._driver.write_bit(coil.id, 1 if value else 0)

    async def async_write_coil(self, coil: CoilEntity, value: bool):
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._write_coil, coil, value
            )

    async def async_read_coil(self, coil: CoilEntity) -> bool:
        async with self._lock:
            return await self.hass.async_add_executor_job(
                self._read_coil, coil
            )



class ModbusDevice:

    def __init__(self, port: ModbusPort, config: ConfigType):
        self.port = port
        self.slave_id = config.get(CONF_SLAVE_ID)

        self.coils = {}
        for coil_config in config.get(CONF_COILS):
            entity = CoilEntity(self, coil_config)
            self.coils[entity.id] = entity

    def __str__(self):
        return f"<ModbusDevice {self.port.name}:{self.slave_id}>"


class CoilEntity(SwitchEntity):

    def __init__(self, device: ModbusDevice, config: ConfigType):
        self.device = device
        self.id = config.get(CONF_ID)
        self._attr_name = config.get(CONF_NAME)
        self._attr_is_on = False
        self._attr_unique_id = f"{DOMAIN}-{self.device.port.name}-{self.device.slave_id}-{self.id}"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.port.async_write_coil(self, True)
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.port.async_write_coil(self, False)
        self._attr_is_on = False
