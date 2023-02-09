# Sora

High power rocket data acquisition system with apogee detection for the RP2040 microcontroller written in microPython

- [Sora](#sora)
  - [Description](#description)
    - [features](#features)
  - [Getting Started](#getting-started)
    - [Hardware](#hardware)
    - [Dependencies](#dependencies)
    - [Usage](#usage)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Description

Sora is a data acquisition program based on the [DPS310 Precision Barometric Pressure/Altitude sensor](https://www.adafruit.com/product/4494) and the [ISM330DHCX - 6 DoF IMU - Accelerometer and Gyroscope](https://www.adafruit.com/product/4502) and runs on a [PIM560, Pimoroni Pico LiPo - 16MB](https://shop.pimoroni.com/products/pimoroni-pico-lipo?variant=39335427080275).
The DPS310 sensor is used to track the altitude of the rocket during flight.
The ISM330DHCX sensor is used to track the acceleration and angular velocity in 3 axis.
All of the flight data is logged to the flight-data file (altitude, pressure, temperature, acceleration and angular velocity).
To allow for easy activation and deactivation, a reed switch is used to trigger the program. This requires the use of a decently strong magnet to activate the reed switch through the fuselage of the rocket. The recommended use of the reed switch is to activate the avionics after the rocket is installed on the launchpad to prevent a false detection of the powered ascent stage.

### features

- Flight stage detection
- Apogee detection
- Activation with a reed switch
- Sound notifications with a buzzer
- Logging of altitude from ground level
- Logging of 3 axis acceleration
- Logging of 3 axis angular velocity

All the values are recorded in metric units.

- Altitude is in meters(m) from ground level
- Pressure is in hectoPascal(hPa)/millibar(mb) at current location/elevation
- Temperature is in Celsius(°C) at current location/elevation
- Acceleration is in meters per second squared (m/s²)
- Velocity is in meters per second(m/s)
- Angular velocity is in degres per second(°/s)

## Getting Started

### Hardware

- [PIM560, Pimoroni Pico LiPo - 16MB](https://shop.pimoroni.com/products/pimoroni-pico-lipo?variant=39335427080275)
- [DPS310 barometric pressure sensor](https://www.adafruit.com/product/4494)
- [ISM330DHCX accelerometer and gyroscope sensor](https://www.adafruit.com/product/4502)
- Reed switch
- Push button
- Buzzer
- 3.7V 400mAh battery
- Qwiic/Stemma QT cables

### Dependencies

- [CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython)

### Usage

- Install [CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython) on your pico
- Copy the .py file to the CIRCUITPY drive
- Create a data folder at the root of the CIRCUITPY drive
- Run PUTTY with the serial port of your device to access REPL(console)
- Before launch update the sea level pressure in the init function of the altimeter class to the current weather report

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

- [DomPizzie/README-Template.md](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
- [Adafruit tutorial for the DPS310 sensor](https://learn.adafruit.com/adafruit-dps310-precision-barometric-pressure-sensor/python-circuitpython)
- [Adafruit tutorial for the ISM330DHCX sensor](https://learn.adafruit.com/lsm6dsox-and-ism330dhc-6-dof-imu/)
