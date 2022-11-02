"""Accelerometer sensor module"""

import board
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX
from adafruit_lsm6ds import Rate, AccelRange, GyroRange


class Accelerometer(object):
    """Altimeter API using the DPS310 sensor"""

    def __init__(self):
        self.init_accelerometer()

    def init_accelerometer(self):
        """Initialize settings for the ISM330DHCX sensor"""
        print("Initializing accelerometer...")
        i2c = board.I2C()  # uses board.SCL and board.SDA
        self._sensor = ISM330DHCX(i2c)
        self._sensor.accelerometer_range = AccelRange.RANGE_16G
        self._sensor.accelerometer_data_rate = Rate.RATE_1_66K_HZ
        self._sensor.gyro_range = GyroRange.RANGE_1000_DPS
        self._sensor.gyro_data_rate = Rate.RATE_208_HZ

        self._gravity_x = 0.0
        self._gravity_y = 0.0
        self._gravity_z = 0.0
        print("Accelerometer initalization finished!")

    def get_accel(self) -> tuple:
        """Get current acceleration from accelerometer"""
        return self._sensor.acceleration

    def get_corrected_accel(self) -> tuple:
        """Get current acceleration from accelerometer"""
        accel_x, accel_y, accel_z = self._sensor.acceleration

        ALPHA = 0.8

        self._gravity_x = ALPHA * self._gravity_x + (1 - ALPHA) * accel_x
        self._gravity_y = ALPHA * self._gravity_y + (1 - ALPHA) * accel_y
        self._gravity_z = ALPHA * self._gravity_z + (1 - ALPHA) * accel_z

        linear_acceleration_x = accel_x - self._gravity_x
        linear_acceleration_y = accel_y - self._gravity_y
        linear_acceleration_z = accel_z - self._gravity_z

        return linear_acceleration_x, linear_acceleration_y, linear_acceleration_z

    def get_gyro(self) -> tuple:
        """Get current angular velocity from gyroscope"""
        return self._sensor.gyro
    
    def calibrate(self):
        """Calibrate the accelerometer"""
        print("Calibrating accelerometer...")
        for _ in range(20):
            accel_x, accel_y, accel_z = self.get_corrected_accel()
        print("Calibration finished!")
        
