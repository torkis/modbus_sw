"""Constants for the Modbus Switch integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "modbus_sw"

CONF_BAUDRATE: Final = "baudrate"
CONF_STOPBITS: Final = "stopbits"
CONF_BYTESIZE: Final = "bytesize"
CONF_PARITY: Final = "parity"
CONF_RTSMODE: Final = "rtsmode"
CONF_RTSPIN: Final = "rtspin"
CONF_RTSDELAY: Final = "rtsdelay"
CONF_SLAVE_ID: Final = "slave_id"
CONF_COILS: Final = "coils"
CONF_COIL: Final = "coil"

PORTS: Final = "ports"
DEVICES: Final = "devices"
COILS: Final = "coils"
