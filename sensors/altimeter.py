"""Altimeter module"""

import board
from adafruit_dps310.advanced import DPS310_Advanced as DPS310
from adafruit_dps310.advanced import Rate as DPS310_RATE
from adafruit_dps310.advanced import Mode as DPS310_MODE
from adafruit_dps310.advanced import SampleCount as DPS310_SAMPLE_COUNT


class Altimeter(object):
    """Altimeter API using the DPS310 sensor"""

    def __init__(self):
        self.init_altimeter()

    def init_altimeter(self):
        """Initialize settings for the DPS310 sensor"""
        print("Initializing altimeter...")
        i2c = board.I2C()  # uses board.SCL and board.SDA
        self._sensor = DPS310(i2c)
        self._sensor.reset()
        self._sensor.pressure_oversample_count = DPS310_SAMPLE_COUNT.COUNT_4
        self._sensor.pressure_rate = DPS310_RATE.RATE_128_HZ
        self._sensor.temperature_oversample_count = DPS310_SAMPLE_COUNT.COUNT_4
        self._sensor.temperature_rate = DPS310_RATE.RATE_128_HZ
        self._sensor.mode = DPS310_MODE.CONT_PRESTEMP
        self._sensor.sea_level_pressure = 1013.25 # 1013.25 hPa is the standard sea level pressure
        self._sensor.wait_temperature_ready()
        self._sensor.wait_pressure_ready()
        print("Altimeter initalization finished!")

    def get_sensor_data(self) -> tuple:
        """Get current sensor data from altimeter"""
        return (self._sensor.pressure, self._sensor.altitude, self._sensor.temperature)
