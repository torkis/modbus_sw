from .modbus_core import ModbusCore
from .modbus_core import ffi as ffiModbusCore
from cffi import FFI

ffi = FFI()
ffi.include(ffiModbusCore)
ffi.cdef(
    """
    modbus_t* modbus_new_rtu_rs485pi(const char *device, int baud,
		char parity, int data_bit, int stop_bit, char rts_mode, int rts_pin, int rts_delayus);
    void modbus_free_rtu_rs485pi(modbus_t *ctx);
"""
)

libmodbus_rs485 = ffi.dlopen("modbus-rs485pi")


class ModbusRtu(ModbusCore):
    def __init__(self, device, baud, parity, data_bit, stop_bit, rts_mode, rts_pin, rts_delayus):
        self.ctx = libmodbus_rs485.modbus_new_rtu_rs485pi(device.encode(), baud, parity.encode(), data_bit, stop_bit,
                                                          rts_mode.encode(), rts_pin, rts_delayus)

    def __del__(self):
        libmodbus_rs485.modbus_free_rtu_rs485pi(self.ctx)
