from components.prosumer.pv import PV
import matplotlib.pyplot as plt
from config.config import PROJ_PATH
import os

import matplotlib.pyplot as plt

def test_pv_simulation():
    from datetime import datetime, timedelta
    from utilities.simulation_period import SimulationPeriod

    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 1, 5),
        resolution=timedelta(minutes=15)
    )
    data_path = PROJ_PATH / "data" / "building"
    # Define the parameters for the PV system
    area_m3 = 10.0
    angle_deg = 30.0
    orientation_deg = 180.0
    epw_file = os.path.join(data_path, "DEU_Stuttgart.107380_IWEC.epw") # replace with your actual file path

    # Initialize the PV system
    pv_system = PV(simulation_period, area_m3, angle_deg, orientation_deg, epw_file)

    # Run the model and get the power output for all timestamps
    power_output = pv_system.power_kw_series()

    # Plot the power output over time
    plt.figure(figsize=(12, 6))
    plt.plot(power_output)
    plt.xlabel('Time step')
    plt.ylabel('Power Output (kW)')
    plt.title('PV Generation Over Time')
    plt.show()

# test_pv_simulation()


def test_pv_power_kw():
    from datetime import datetime, timedelta
    from utilities.simulation_period import SimulationPeriod

    # Define the simulation period
    start_iso = "2022-01-01T00:00:00"
    end_iso = "2022-01-31T00:00:00"
    resolution_seconds = 3600.0  # One hour
    simulation_period = SimulationPeriod.from_iso(start_iso, end_iso, resolution_seconds)

    data_path = PROJ_PATH / "data" / "building"
    # Define the parameters for the PV system
    area_m3 = 10.0
    angle_deg = 30.0
    orientation_deg = 180.0
    epw_file = os.path.join(data_path, "DEU_Stuttgart.107380_IWEC.epw")  # replace with your actual file path

    # Initialize the PV system
    pv_system = PV(simulation_period, area_m3, angle_deg, orientation_deg, epw_file)

    # Simulate the PV system for each hour in a day
    timestamp = simulation_period.start
    for i, timestamp in enumerate(simulation_period):
        power = pv_system.power_kw(timestamp)
        print(f"Time: {timestamp}, Power: {power} kW")
        timestamp += timedelta(seconds=resolution_seconds)

# test_pv_power_kw()