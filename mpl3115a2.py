#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import subprocess

try:
    from periphery import I2C
except ImportError:
    pass

try:
    import pigpio
except ImportError:
    pass


class RPiHwI2C(object):

    """ python-perhiphery based HW I2C driver
    """

    def open_bus(self):
        """
        Creates a hardware I2C handle. 
        """

        self.handle = I2C("/dev/i2c-1")

    def close_bus(self):
        """
        Closes an open HW handle.
        """
        self.handle.close()

    def read(self, address, pointer_reg, read_bytes):
        """
        Performs a standard I2C read operation on a
        particular address. Requires the 7-bit I2C address,
        the pointer register to write to, and the number 
        of bytes to read from the pointer register.
        """
        read_bytes += 1

        placeholder_bytes = []
        for i in range(0, read_bytes):
            placeholder_bytes.append(0x00)

        msgs = [I2C.Message([pointer_reg]), I2C.Message(
            placeholder_bytes, read=True)]
        self.handle.transfer(address, msgs)

        output = bytearray(msgs[1].data[0:6])
        return output

    def write(self, address, pointer_reg, data_array):
        """
        Performs a standard I2C write opreation on a particular
        address. Requires the 7-bit I2C address, the pointer
        register, and a data array of the data package to send.

        """
        msgs = [I2C.Message([pointer_reg, data_array], read=False)]
        self.handle.transfer(address, msgs)


class PigpioI2CBitBang(object):

    """
    PIGPIO Bitbang I2C Helper Class
    Provides device specific I2C interface
    instructions to PIGPIO daemon. 
    """

    # GPIO configuration and frequency constants
    SDA = 6
    SCL = 13
    CF = 80000

    # PIGPIO bitbang constants
    BB_END = 0
    BB_ESCAPE = 1
    BB_START = 2
    BB_STOP = 3
    BB_ADDRESS = 4
    BB_FLAGS = 5
    BB_READ = 6
    BB_WRITE = 7

    def __init__(self):
        """
        Initalize the pigpio library.
        """
        self.pi = pigpio.pi()

    def stop(self):
        """
        Stop pigpio connection
        """
        self.pi.stop()

    def open_bus(self):
        """
        Creates a bitbang handle with a given SDA/SCL GPIO
        pair, and a I2C freqency set by CF.
        """
        self.handle = self.pi.bb_i2c_open(self.SDA, self.SCL, self.CF)

    def close_bus(self):
        """
        Closes an open bitbang handle.
        """
        self.pi.bb_i2c_close(self.SDA)

    def read(self, address, pointer_reg, read_bytes):
        """
        Performs a standard I2C read operation on a
        particular address. Requires the 7-bit I2C address,
        the pointer register to write to, and the number 
        of bytes to read from the pointer register.
        """
        read_bytes += 1
        arg_list = [self.BB_ADDRESS, address, self.BB_START,
                    self.BB_WRITE, self.BB_ESCAPE, pointer_reg,
                    self.BB_START, self.BB_READ, read_bytes,
                    self.BB_STOP, self.BB_END]
        count, data = self.pi.bb_i2c_zip(self.SDA, arg_list)
        return data

    def write(self, address, pointer_reg, data_array):
        """
        Performs a standard I2C write opreation on a particular
        address. Requires the 7-bit I2C address, the pointer
        register, and a data array of the data package to send.
        """
        if type(data_array) is int:
            assert data_array < 256
            data_array = [data_array]
        arg_list = [self.BB_ADDRESS, address, self.BB_START,
                    self.BB_WRITE, len(data_array)+1, pointer_reg
                    ] + data_array + [self.BB_STOP, self.BB_END]
        count, data = self.pi.bb_i2c_zip(self.SDA, arg_list)
        return data


class MPL3115A2(object):

    """
    Freescale MPL3115A2 Driver
    """

    # datasheet constants
    BAR_I2C = 0x60
    WHO_AM_I = 0x0C
    CONTROL_REG_ADDR = 0x26
    BAR_OSR_128 = 0x28
    BAR_ENABLE = 0x29
    DATA_FLAG_ADDR = 0x13
    ENABLE_DATA_FLAG = 0x07
    STATUS_REG = 0x00
    P_MSB = 0x01
    STATUS_RDY = 3
    SOFTWARE_RESET = 0x04

    def __init__(self, i2c_handle):
        """
        Takes in a pigpio I2C channel handle,
        opens the bus, and writes initial 
        configuration to the MPL3115A2.
        """
        self.i2c_handle = i2c_handle
        self.i2c_handle.write(self.BAR_I2C,
                              self.DATA_FLAG_ADDR, self.ENABLE_DATA_FLAG)

    def software_reset(self):
        """
        Performs a software reset of the MPL3115A2.
        Perform a set_ method before re-read.
        """
        self.i2c_handle.write(self.BAR_I2C,
                              self.CONTROL_REG_ADDR, self.SOFTWARE_RESET)
        self.set_barometric()

    def is_alive(self):
        """
        Reads the WHO_AM_I register to
        verify I2C communication.
        """
        raw = self.i2c_handle.read(self.BAR_I2C, self.WHO_AM_I, 0)
        id_bytes = list(raw)
        hex_string = "".join('%02x' % i for i in id_bytes)
        return True if hex_string == 'c4' else False

    def set_barometric(self):
        """
        Sets the MPL3115A2 to return
        barometric pressure in Pascals.
        """
        self.i2c_handle.write(self.BAR_I2C,
                              self.CONTROL_REG_ADDR, self.BAR_OSR_128)
        self.i2c_handle.write(self.BAR_I2C,
                              self.CONTROL_REG_ADDR, self.BAR_ENABLE)

    def ready(self):
        """
        Checks the MPL3115A2 status register to determine
        if the part has completed a measurement and can
        be accessed via I2C.
        """
        data = self.i2c_handle.read(self.BAR_I2C, self.STATUS_REG, 1)
        if len(data) > 0 and data[0] & (1 << self.STATUS_RDY):
            return True
        return False

    def get_data(self):
        """
        Grabs MPL3115A2 data package.
        """
        if not self.ready():
            return None, None
        raw = self.i2c_handle.read(self.BAR_I2C, self.P_MSB, 5)
        return raw

    def package_output(self, raw, measurement):
        """
        Convert raw bitarray output from I2C read into
        pressure, 20 bit unsigned, altitude, 20 bit signed
        with decimal, or temperature 16 bit unsigned.
        measurement      =        1     |      2
        measurement type =    pressure  |  temperature
        """
        if len(raw) != 6:
            return None
        elif measurement == 1:  # pressure case
            pressure = int.from_bytes(raw[0:3],
                                      byteorder='big', signed=False) / 64.0
            return pressure
        elif measurement == 2:  # temperature case
            temperature = int.from_bytes(raw[3:5],
                                         byteorder='big', signed=False) / 256.0
            return temperature


class PressureAPI(object):

    """
    API for MPL3115A2 breakout board. 

    Creates an I2C channel, then
    passes the I2C handle into MPL3115A2
    object for I2C operations.

    Usage:
    PressureAPI.get_pressure()
    PressureAPI.get_temperature()

    Finish with PressureAPI.close()
    """

    def __init__(self, i2c_type):
        """
        Creates a I2C channel.
        i2c_type = 0: Hardware I2C
        i2c_type = 1: Software/Bitbang I2C
        """
        self.i2c_type = i2c_type

        if self.i2c_type == 0:
            self.i2c_channel = RPiHwI2C()
            self.i2c_channel.open_bus()
            self.mpl3115a2 = MPL3115A2(self.i2c_channel)

        if self.i2c_type == 1:
            self.i2c_channel = PigpioI2CBitBang()
            self.i2c_channel.open_bus()
            self.mpl3115a2 = MPL3115A2(self.i2c_channel)

        self.mpl3115a2.set_barometric()
        self.max_loop_iterations = 10

    def close(self):
        """
        Tears down the I2C channel.
        """
        self.i2c_channel.close_bus()

    def check_comms(self):
        """
        Returns current I2C communication status.
        """
        return self.mpl3115a2.is_alive()

    def restart_pigpiod(self):
        """
        Restarts the pigpiod daemon if there is a connection
        timeout.
        Used only with software I2C.
        """
        if self.i2c_type == 1:
            # Exit resources and kill the daemon
            self.i2c_channel.close_bus()
            self.i2c_channel.stop()
            pigpio_kill_string = "sudo pkill pigpiod"
            subprocess.Popen(pigpio_kill_string, shell=True)
            time.sleep(5)

            # Restart the daemon & reinitalize connections
            pigpio_start_string = "sudo pigpiod"
            start = subprocess.Popen(pigpio_start_string, shell=True)
            time.sleep(5)

            self.i2c_channel = PigpioI2CBitBang()
            self.i2c_channel.open_bus()
            self.mpl3115a2 = MPL3115A2(self.i2c_channel)

    def i2c_loop(self, measurement_type):
        """
        Loops through an I2C measurement and attempts to grab data, will
        return data if data package received.
        """
        loop_check = 0
        while loop_check < self.max_loop_iterations:
            raw_data = self.mpl3115a2.get_data()
            output = self.mpl3115a2.package_output(raw_data, measurement_type)
            if output is not None:
                return output
            else:
                loop_check += 1
                time.sleep(1)
                continue

    def get_pressure(self):
        """
        Returns current barometric pressure in Pascals.
        """
        pressure = self.i2c_loop(1)
        if not pressure:
            self.mpl3115a2.software_reset()
            pressure = self.i2c_loop(1)
            if not pressure:
                if self.i2c_type == 1:
                    self.restart_pigpiod()
                    pressure = self.i2c_loop(1)
                    if not pressure:
                        raise ValueError("I2C Timeout Error.")
                raise ValueError("I2C Timeout Error.")
        return pressure

    def get_temperature(self):
        """
        Returns current measured temperature in degrees C.
        """
        temperature = self.i2c_loop(2)
        if not temperature:
            self.mpl3115a2.software_reset()
            temperature = self.i2c_loop(2)
            if not temperature:
                if self.i2c_type == 1:
                    self.restart_pigpiod()
                    temperature = self.i2c_loop(2)
                    if not temperature:
                        raise ValueError("I2C Timeout Error.")
                raise ValueError("I2C Timeout Error.")
        return temperature
