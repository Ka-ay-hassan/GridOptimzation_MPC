from datetime import timedelta, datetime

from components.storages.energetic.electrical.battery import BatterySystem
from utilities.simulation_period import SimulationPeriod


def main() -> None:
    simulation_period = SimulationPeriod(start=datetime.now(), end=datetime.now() + timedelta(days=7),
                                         resolution=timedelta(minutes=1))
    battery = BatterySystem(
        capacity_nom_kwh=100,
        power_nom_kw=50,
        simulation_period=simulation_period
    )
    start_charging = (datetime.now() + timedelta(minutes=500))
    end_charging = (datetime.now() + timedelta(minutes=800))
    start_discharging = (start_charging + timedelta(minutes=500))
    end_discharging = (end_charging + timedelta(minutes=800))
    for timestamp in simulation_period:
        if start_charging < timestamp < end_charging:
            battery.set_power_kw(100, timestamp=timestamp)
        if start_discharging < timestamp < end_discharging:
            battery.set_power_kw(-100, timestamp=timestamp)
    print(battery.soc)
    import matplotlib.pyplot as plt
    battery.data.power_kw.plot(title="power_kw")
    battery.data.loc[:, ("soc", "soh")].plot(title="soc and soh")
    plt.show()


if __name__ == "__main__":
    main()
