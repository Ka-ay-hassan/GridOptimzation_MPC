from __future__ import annotations

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
import random

import numpy as np
import pandas as pd

from components.prosumer.prosumer import Prosumer
from typing import Optional

from config.config import PROJ_PATH
from utilities.simulation_period import SimulationPeriod


class ElectricalLoad(Prosumer):
    _profiles: pd.DataFrame | None = None

    @classmethod
    def _load_profiles_from_file(cls) -> None:
        cls._profiles = pd.read_csv(PROJ_PATH / "data" / "load_profiles" / "load_profiles.csv", index_col="index")
        datetimeindex = pd.date_range(start="2010-01-01", end="2011-01-01",
                                      freq=pd.DateOffset(minutes=15))
        cls._profiles = cls._profiles.set_index(datetimeindex, drop=True)

    @classmethod
    def _get_profile(cls, profile_name: Optional[str] = None) -> pd.Series:
        if cls._profiles is None:
            cls._load_profiles_from_file()
        if profile_name is None:
            return cls._profiles[random.choice(cls._profiles.columns)]
        return cls._profiles[profile_name]

    def __init__(self, yearly_energy_demand_kwh: float, simulation_period: SimulationPeriod,
                 profile_name: Optional[str] = None) -> None:
        super().__init__("ElectricalLoad")
        self.year_energy_demand_kwh = yearly_energy_demand_kwh
        self.simulation_period = simulation_period
        profile = self._get_profile(profile_name)
        self.profile = self._scale_profile(profile)

    def _scale_profile(self, profile: pd.Series) -> pd.Series:
        yearly_energy_kwh = profile.sum() / 4  # load_profiles are in 15 min resolution
        profile *= self.year_energy_demand_kwh / yearly_energy_kwh
        return profile.resample(
            pd.Timedelta(seconds=self.simulation_period.resolution_seconds)
        ).interpolate("linear")

    def power_kw(self, timestamp: datetime) -> float:
        base_year = 2010
        timestamp_ = timestamp - relativedelta(years=timestamp.year - base_year)
        return self.profile.loc[timestamp_]


def test_load() -> None:
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2023, 1, 1),
        resolution=timedelta(minutes=1)
    )
    load = ElectricalLoad(
        yearly_energy_demand_kwh=1000,
        simulation_period=simulation_period,
    )
    import math
    assert math.isclose(load.year_energy_demand_kwh, load.profile.sum() / 60, rel_tol=0.001, abs_tol=0.05)

    powers = np.array([load.power_kw(timestamp) for timestamp in simulation_period])
    df = pd.DataFrame(powers, index=simulation_period.datetimeindex())
    import matplotlib.pyplot as plt
    df.plot()
    plt.show()


if __name__ == "__main__":
    test_load()
