from __future__ import annotations

import logging
import asyncio
from async_timeout import timeout
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from homeassistant.const import (
    CONF_NAME,
    CONF_ID,
    CONF_DEVICES,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
)

from .const import *

from .modbus_rs485pi import ModbusRtu

_LOGGER = logging.getLogger(__name__)


class ModbusPort:
    """Represents a hardware based modbus RS485 port. Contains the configured devices.
    This object performs all modbus related calls for the devices under the port."""

    def __init__(self, hass: HomeAssistant, config: ConfigType):
        self._hass = hass
        self.name = config.get(CONF_NAME)

        # configure devices
        self.devices = []
        if config.get(CONF_DEVICES):
            for device_config in config.get(CONF_DEVICES):
                self.devices.append(ModbusDevice(self, device_config))

        # lock for modbus port calls, because these can't be concurrent
        self._lock = asyncio.Lock()
        self._auto_update_remover = None

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
        """Read state of coil with modbus call"""
        self._driver.set_slave(coil.device.slave_id)
        return bool(self._driver.read_bits(coil.id, 1)[0])

    def _write_coil(self, coil: CoilEntity, value: bool) -> None:
        """Write state of coil with modbus call"""
        self._driver.set_slave(coil.device.slave_id)
        self._driver.write_bit(coil.id, 1 if value else 0)

    async def async_read_coil(self, coil: CoilEntity) -> bool:
        """Read state of coil entity"""
        async with self._lock:
            return await self.hass.async_add_executor_job(
                self._read_coil, coil
            )

    async def async_write_coil(self, coil: CoilEntity, value: bool) -> None:
        """Write state of coil entity"""
        async with self._lock:
            await self._hass.async_add_executor_job(
                self._write_coil, coil, value
            )

    def _update_device_coils(self, device: ModbusDevice) -> None:
        """Update device coil state with modbus call."""
        start = min(device.coils.keys())
        count = max(device.coils.keys()) + 1 - start
        _LOGGER.info(f"update coils of {device} from:{start} count:{count}")
        self._driver.set_slave(device.slave_id)
        result = self._driver.read_bits(start, count)
        for i, val in enumerate(result):
            if i in device.coils:
                _LOGGER.info(f"{i}:{val}")
                device.coils[start + i].set_is_on(bool(val))

    def _update_state(self) -> None:
        """Update all device state in port."""
        for device in self.devices:
            self._update_device_coils(device)

    async def _async_update_state(self, event_time: timedelta = None) -> None:
        """Update all device state"""
        async with self._lock:
            async with timeout(10):
                await self._hass.async_add_executor_job(self._update_state)

    async def async_enable_auto_update(self, interval: timedelta, call_update: bool = False):
        """Enable auto update function for all devices in port."""
        self._auto_update_remover = async_track_time_interval(
            self._hass, self._async_update_state, interval)

        # remove auto updater callback
        async def async_stop_listen_task(event):
            _LOGGER.info(f"Remove {self} autoupdater")
            self._auto_update_remover()

        # and register it
        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop_listen_task)

        # call update after registration if needed
        if call_update:
            await self._async_update_state()


class ModbusDevice:
    """Represents a device in a modbus port with slave id. The device can contains coils and sensors."""

    def __init__(self, port: ModbusPort, config: ConfigType):
        self.port = port
        self.slave_id = config.get(CONF_SLAVE_ID)

        # configure coils
        self.coils = {}
        for coil_config in config.get(CONF_COILS):
            entity = CoilEntity(self, coil_config)
            self.coils[entity.id] = entity

    def __str__(self):
        return f"<ModbusDevice {self.port.name}:{self.slave_id}>"


class CoilEntity(SwitchEntity):
    """Represents a coil in the device as simple switch entity."""

    def __init__(self, device: ModbusDevice, config: ConfigType):
        self.device = device
        self.id = config.get(CONF_ID)
        self._attr_name = config.get(CONF_NAME)
        self._attr_is_on = False
        self._attr_unique_id = f"{DOMAIN}-{self.device.port.name}-{self.device.slave_id}-{self.id}"
        self._attr_should_poll = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.port.async_write_coil(self, True)
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.port.async_write_coil(self, False)
        self._attr_is_on = False

    def set_is_on(self, value: bool):
        """Set the state without calling modbus. Called by the update state from ModbusPort"""
        if value != self._attr_is_on:
            self._attr_is_on = value
            # update ha state if device is initialized
            if self.hass:
                self.async_write_ha_state()
                _LOGGER.info(f"{self} state updated")

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.async_write_ha_state)
