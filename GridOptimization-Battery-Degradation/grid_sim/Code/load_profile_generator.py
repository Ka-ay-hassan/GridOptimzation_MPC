from blpg import BuildingProfileGenerator, BuildingUsage
from timeseries import TimeSeries
import pandas as pd
from datetime import datetime, timedelta


def create_profiles(loads: pd.DataFrame) -> pd.DataFrame:
    profiles = list()
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 8)
    resolution = timedelta(minutes=15)
    for load in loads:
        profiles.append(generator(load.building_type, load.yearly_energy, start, end, resolution))
    return pd.concat(profiles)


def generator(
        building_type: str, yearly_energy_kwh: int, start: datetime, end: datetime, resolution: timedelta
) -> pd.DataFrame:
    simulation_period = TimeSeries(start=start, end=end, resolution=resolution)
    building_usage = get_building_type(building_type)
    gen = BuildingProfileGenerator(
        simulation_period=simulation_period,
        building_usage=building_usage,
        n_profiles=1,
        yearly_energy_kwh=yearly_energy_kwh
    )
    return gen.run()


def get_building_type(building_type: str) -> BuildingUsage:
    if building_type == "business":
        return BuildingUsage.BUSINESS
    elif building_type == "agriculture":
        return BuildingUsage.AGRICULTURE
    elif building_type == "household":
        return BuildingUsage.HOUSEHOLD
    elif building_type == "industrial":
        return BuildingUsage.INDUSTRIAL
    else:
        return BuildingUsage.BUSINESS  # default


if __name__ == "__main__":
    # data = pd.read_excel("")
    # create_profiles()
    # run the simulation:
    # profiles = generator.run(show_progress_bar=True)  # tqdm must be installed for show_progress_bar=True
    # plot results:
    # simple_plot(profiles, show=True)
    pass
