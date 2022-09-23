"""The flight manager"""

import time
import asyncio
import os

from sensors.accelerometer import Accelerometer
from sensors.altimeter import Altimeter

FLIGHT_STAGES = (
    "LAUNCHPAD",
    "POWERED_ASCENT",
    "COASTING_ASCENT",
    "APOGEE",
    "DESCENT",
    "LANDING",
)


class FlightManager:
    """The flight manager uses data from the altimeter and accelerometer to determine the flight stage"""

    def __init__(self) -> None:
        self.altimeter = Altimeter()
        self.accelerometer = Accelerometer()

        self.flight_stage = FLIGHT_STAGES[
            0
        ]  # Set the initial flight stage to LAUNCHPAD
        self.initial_altitude: float = 0.0
        self.max_altitude: float = 0.0
        self.max_velocity_y: float = 0.0
        self.max_acceleration_y: float = 0.0

        self.is_fs_full = False

    async def fly(self, event, is_development) -> None:
        """State machine to determine the current flight stage"""
        velocity_y: float = 0.0
        self.initial_altitude: float = self.altimeter.get_sensor_data()[0]
        print("Flight stage: %s", self.flight_stage)

        self.accelerometer.calibrate()

        # Create and open the flight data file
        if not is_development:
            try:
                self.flight_data_file = open("/data/flight-data.csv", "w")
                self.flight_data_file.write(
                    "Timestamp,Altitude,Pressure,Temperature,Velocity_X,Velocity_Y,Velocity_Z,Acceleration_X,Acceleration_Y,Acceleration_Z,Angular_Velocity_X,Angular_Velocity_Y,Angular_Velocity_Z,FlightStage\n"
                )
                print("Opened flight data file...")
            except OSError as err:
                # if the filesystem isn't writeable, skip logging to file
                print("Unable to open flight data file: %s", err)
                print("Switching to development mode...")
                is_development = True

        while event.is_set():

            start_time = time.monotonic()
            # Get the accelerometer data
            (
                self.accel_x,
                self.accel_y,
                self.accel_z,
                gyro_x,
                gyro_y,
                gyro_z,
            ) = self.get_accel_data()
            # Get the altimeter data
            altitude, pressure, temperature = self.altimeter.get_sensor_data()
            velocity_x, velocity_y, velocity_z = self.get_velocity(
                time.monotonic() - start_time
            )

            # Check running move and if file isn't bigger than 12MB to prevent overfilling the filesystem
            if not is_development:
                "In production mode, log the flight data to a file"
                self.log_flight_data(
                    altitude,
                    pressure,
                    temperature,
                    self.accel_x,
                    self.accel_y,
                    self.accel_z,
                    velocity_x,
                    velocity_y,
                    velocity_z,
                    gyro_x,
                    gyro_y,
                    gyro_z,
                    self.flight_stage,
                    os.stat("/data/flight_data.csv")[
                        6
                    ],  # get the file size in bytes
                )

            else:
                print(
                    f"{time.monotonic()},{altitude:.2f},{pressure:.2f},{temperature:.2f},{velocity_x:.4f},{velocity_y:.4f},{velocity_z:.4f},{self.accel_x:.4f},{self.accel_y:.4f},{self.accel_z:.4f},{gyro_x:.4f},{gyro_y:.4f},{gyro_z:.4f},{self.flight_stage}"
                )

            # Update the maximum values
            self.max_altitude = max(self.max_altitude, altitude)
            self.max_acceleration_y = max(self.max_acceleration_y, self.accel_y)
            self.max_velocity_y = max(self.max_velocity_y, velocity_y)

            # Determine the current flight stage
            if self.flight_stage == FLIGHT_STAGES[0]:  # LAUNCHPAD
                if self.accel_y > 1.0:  # Powered ascent detection
                    print(f"Powered ascent detected! at {time.monotonic()}s")
                    self.flight_stage = FLIGHT_STAGES[1]
                    print(f"Flight stage: {self.flight_stage}")
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[1]:  # POWERED_ASCENT
                if (self.accel_y <= 1.0) and (
                    velocity_y > 1.0
                ):  # Coasting ascent detection
                    print(f"Coasting ascent detected! at {time.monotonic()}s")
                    self.flight_stage = FLIGHT_STAGES[2]
                    print(f"Flight stage: {self.flight_stage}")
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[2]:  # COASTING_ASCENT
                if velocity_y <= 1.0:  # Apogee detection
                    self.apogee_altitude = altitude
                    print(
                        f"Apogee detected at {self.apogee_altitude}m at {time.monotonic()}s"
                    )
                    self.flight_stage = FLIGHT_STAGES[3]
                    print(f"Flight stage: {self.flight_stage}")
                    # sleep for 1 second to prevent false detection of descent because of the separation
                    await asyncio.sleep(1)
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[3]:  # APOGEE
                if (
                    altitude <= self.apogee_altitude - 15.0
                ):  # Descent detection when 15 meters below apogee
                    print(f"Descent detected! at {time.monotonic()}s")
                    self.flight_stage = FLIGHT_STAGES[4]
                    print(f"Flight stage: {self.flight_stage}")
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[4]:  # DESCENT
                if (
                    self.initial_altitude - 100.0
                    <= altitude
                    <= self.initial_altitude + 100.0
                ) and (
                    (-1.0 <= velocity_x <= 1.0)
                    and (-1.0 <= velocity_y <= 1.0)
                    and (-1.0 <= velocity_z <= 1.0)
                ):  # Touchdown detection
                    print(f"Touchdown detected! at {time.monotonic()}")
                    self.flight_stage = FLIGHT_STAGES[5]
                    print(f"Flight stage: {self.flight_stage}")
                await asyncio.sleep(0)

        print(f"Flight stage: {self.flight_stage}")
        if self.is_fs_full:
            self.flight_data_file.write("Filesystem full, data logging stopped")
        if not is_development:
            try:
                self.flight_data_file.close()
            except OSError as err:
                print("Unable to close flight data file: %s", err)

    def get_accel_data(self) -> tuple:
        """Get the accelerometer data"""
        accel_x, accel_y, accel_z = self.accelerometer.get_corrected_accel()
        gyro_x, gyro_y, gyro_z = self.accelerometer.get_gyro()

        return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z

    def get_velocity(self, dt) -> tuple:
        """Get the velocity for all axis"""
        accel_x_filtered = 0.0
        accel_y_filtered = 0.0
        accel_z_filtered = 0.0
        velocity_x: float = 0.0
        velocity_y: float = 0.0
        velocity_z: float = 0.0
        S = 0.75  # filter/smoothing factor

        # Filter accleleration data
        accel_x_filtered = accel_x_filtered * S + self.accel_x * (1 - S)
        accel_y_filtered = accel_y_filtered * S + self.accel_y * (1 - S)
        accel_z_filtered = accel_z_filtered * S + self.accel_z * (1 - S)

        # integrate just using a reimann sum
        velocity_x += accel_x_filtered * dt
        velocity_y += accel_y_filtered * dt
        velocity_z += accel_z_filtered * dt

        return velocity_x, velocity_y, velocity_z

    def get_max_values(self) -> tuple:
        """Returns the maximum altitude"""
        return (
            self.max_altitude - self.initial_altitude,
            self.max_velocity_y,
            self.max_acceleration_y,
        )

    def log_flight_data(
        self,
        altitude,
        pressure,
        temperature,
        accel_x,
        accel_y,
        accel_z,
        velocity_x,
        velocity_y,
        velocity_z,
        gyro_x,
        gyro_y,
        gyro_z,
        flight_stage,
        file_size,
    ) -> None:

        try:
            if file_size <= 12000000:
                # Timestamp,Altitude,Pressure,Temperature,Velocity_X,Velocity_Y,Velocity_Z,Acceleration_X,Acceleration_Y,Acceleration_Z,FlightStage
                self.flight_data_file.write(
                    f"{time.monotonic()},{altitude:.2f},{pressure:.2f},{temperature:.2f},{velocity_x:.4f},{velocity_y:.4f},{velocity_z:.4f},{accel_x:.4f},{accel_y:.4f},{accel_z:.4f},{gyro_x:.4f},{gyro_y:.4f},{gyro_z:.4f},{flight_stage}\n"
                )
            else:
                self.is_fs_full = True
        except OSError:  # Typically when the filesystem isn't writeable...
            print("Filesystem not writeable, skipping flight data logging")
        except Exception as e:
            print("Error writing to filesystem: %s", e)
            raise e
