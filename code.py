"""Main system for Sora"""

import asyncio
import digitalio
from analogio import AnalogIn
import board
import alarm

from flightManager import FlightManager
from utils.notify import Notify
from utils.reed import Reed


async def main():
    is_development = False

    bat_sense = AnalogIn(board.BAT_SENSE)
    usb_sense = digitalio.DigitalInOut(board.VBUS_DETECT)
    usb_sense.direction = digitalio.Direction.INPUT

    # Check if filesystem is writable
    try:
        with open("/data/flight-data.csv", "a") as file:
            pass
    except OSError:  # Typically when the filesystem isn't writeable...
        is_development = True
    finally:
        if is_development:
            print("Running in dev mode")
            led = digitalio.DigitalInOut(board.GP25)
            led.direction = digitalio.Direction.OUTPUT
            led.value = True
        else:
            print("Running in prod mode")

    # Logs the battery charge state
    asyncio.run(check_battery(bat_sense, usb_sense))

    notify = Notify()
    flight_manager = FlightManager()
    reed = Reed()

    # wait_for reed switch task to complete
    print("Waiting for reed switch to be triggered...")
    reed_alarm = alarm.pin.PinAlarm(pin=board.GP16, value=False, pull=True)
    alarm.light_sleep_until_alarms(reed_alarm)
    print("Reed switch triggered!")

    # Notify the user that the reed switch was activated
    asyncio.run(notify.buzz(1300, 1024, 1.5))

    # # Set the event to True
    # print("Setting event to True...")
    reed.async_event.set()

    # Start the flight manager task
    print("Run flight manager task...")
    flight_manager_task = asyncio.create_task(
        flight_manager.fly(reed.async_event, is_development)
    )
    asyncio.gather(flight_manager_task)
    asyncio.run(reed.wait(board.GP16))

    # Notify the user that the flightManager is stopping
    asyncio.run(notify.buzz(1000, 1024, 1.5))

    # Logging the max altitude
    max_altitude, max_velocity_y, max_acceleration_y = flight_manager.get_max_values()
    print(f"Max altitude : {max_altitude:.4f}m")
    print(f"Max velocity y axis: {max_velocity_y:.4f}m/s")
    print(f"Max acceleration y axis : {max_acceleration_y:.4f}m/s²")

    # Write the max values to a file for easy access
    if not is_development:
        with open("/data/max_data.txt", "w") as max_data_file:
            max_data_file.write(f"Max altitude : {max_altitude:.4f}m")
            max_data_file.write(f"Max velocity y : {max_velocity_y:.4f}m")
            max_data_file.write(f"Max acceleration y : {max_acceleration_y:.4f}m")
    print("End of flight")


async def check_battery(vsys, charging_pin):
    conversion_factor = 3 * 3.3 / 65535
    full_battery = 4.2  # reference voltages for a full/empty battery, in volts
    empty_battery = 2.8  # the values could vary by battery size/manufacturer so you might need to adjust them

    if charging_pin.value == 1:
        print("Charging...")
    else:
        print("On battery power...")

    # convert the raw ADC read into a voltage, and then a percentage
    voltage = vsys.value * conversion_factor
    percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
    if percentage > 100:
        percentage = 100.0

    print(f"Battery at {percentage:.2f}%...")


if __name__ == "__main__":
    asyncio.run(main())
