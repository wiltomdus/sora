"""The flight manager"""

import time
import asyncio

from sensors.accelerometer import Accelerometer
from sensors.altimeter import Altimeter

FLIGHT_STAGES = (
    "LAUNCHPAD",
    "POWERED_ASCENT",
    "COASTING_ASCENT",
    "APOGEE",
    "DESCENT",
    "LANDED",
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

    async def fly(self, event, is_development) -> None:
        """State machine to determine the current flight stage"""
        velocity_y: float = 0.0
        self.initial_altitude = self.altimeter.get_sensor_data()[1]
        print("Flight stage: %s", self.flight_stage)

        # skip first 20 iterations to allow the acceleration gravity correction to stabilize
        print("Starting aceleration stabilisation...")
        for _ in range(20):
            (
                self.accel_x,
                self.accel_y,
                self.accel_z,
                gyro_x,
                gyro_y,
                gyro_z,
            ) = self.get_accel_data()
            await asyncio.sleep(0)

        if not is_development:
            try:
                self.flight_data_file = open("/data/flight-data.csv", "w")
                self.flight_data_file.write(
                    "Timestamp,Altitude,Pressure,Temperature,Velocity_X,Velocity_Y,Velocity_Z,Acceleration_X,Acceleration_Y,Acceleration_Z,FlightStage\n"
                )
                print("Opened flight data file...")
            except OSError as err:
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
            pressure, altitude, temperature = self.altimeter.get_sensor_data()
            velocity_x, velocity_y, velocity_z = self.get_velocity(
                time.monotonic() - start_time
            )

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
                    self.flight_stage,
                )

            else:
                print(
                    f"{time.monotonic()},{altitude:.2f},{pressure:.2f},{temperature:.2f},{velocity_x:.4f},{velocity_y:.4f},{velocity_z:.4f},{self.accel_x:.4f},{self.accel_y:.4f},{self.accel_z:.4f},{self.flight_stage}"
                )

            # Update the maximum values
            self.max_altitude = max(self.max_altitude, altitude)
            self.max_acceleration_y = max(self.max_acceleration_y, self.accel_y)
            self.max_velocity_y = max(self.max_velocity_y, velocity_y)

            # Determine the current flight stage
            if self.flight_stage == FLIGHT_STAGES[0]:  # LAUNCHPAD
                if self.accel_y > 5.0:  # Acceleration threshold for takeoff
                    print("Powered ascent detected!")
                    self.flight_stage = FLIGHT_STAGES[1]
                    print(f"Flight stage: {self.flight_stage}")
                    continue
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[1]:  # POWERED_ASCENT
                if (self.accel_y < 0.5) and (velocity_y > 0.5):
                    print("Coasting ascent detected!")
                    self.flight_stage = FLIGHT_STAGES[2]
                    print(f"Flight stage: {self.flight_stage}")
                    continue
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[2]:  # COASTING_ASCENT
                if velocity_y <= 1:
                    print(f"Apogee detected at {altitude}m")
                    self.flight_stage = FLIGHT_STAGES[3]
                    print(f"Flight stage: {self.flight_stage}")
                    # sleep for 1 second to prevent false detection of descent # because of the seperation
                    await asyncio.sleep(1)
                    continue
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[3]:  # APOGEE
                if (-1.0 <= self.accel_y <= 1.0) and (velocity_y > 1):
                    print("Descent detected!")
                    self.flight_stage = FLIGHT_STAGES[4]
                    print(f"Flight stage: {self.flight_stage}")
                    continue
                await asyncio.sleep(0)
            elif self.flight_stage == FLIGHT_STAGES[4]:  # DESCENT
                if (pressure >= 1000.0) and (
                    (-1.0 <= velocity_x <= 1.0)
                    and (-1.0 <= velocity_y <= 1.0)
                    and (-1.0 <= velocity_z <= 1.0)
                ):
                    print("Touchdown detected!")
                    self.flight_stage = FLIGHT_STAGES[5]
                    print(f"Flight stage: {self.flight_stage}")
                    continue
                await asyncio.sleep(0)

        print(f"Flight stage: {self.flight_stage}")
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

    def get_alti_data(self) -> tuple:
        """Get the altimeter data"""
        altitude = self.altimeter.get_altitude()
        pressure = self.altimeter.get_pressure()
        temperature = self.altimeter.get_temperature()

        return altitude, pressure, temperature

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

    def get_max_values(self):
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
        flight_stage,
    ):
        try:
            # Timestamp,Altitude,Pressure,Temperature,Velocity_X,Velocity_Y,Velocity_Z,Acceleration_X,Acceleration_Y,Acceleration_Z,FlightStage
            self.flight_data_file.write(
                f"{time.monotonic()},{altitude:.2f},{pressure:.2f},{temperature:.2f},{velocity_x:.4f},{velocity_y:.4f},{velocity_z:.4f},{accel_x:.4f},{accel_y:.4f},{accel_z:.4f},{flight_stage}\n"
            )
        except OSError:  # Typically when the filesystem isn't writeable...
            print("Filesystem not writeable, skipping flight data logging")
        except Exception as e:
            print("Error writing to filesystem: %s", e)
            raise e
