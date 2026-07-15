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


class DHWLoad(Prosumer):
    _profiles: pd.DataFrame | None = None

    @classmethod
    def _load_profiles_from_file(cls) -> None:
        cls._profiles = pd.read_csv(PROJ_PATH / "data" / "load_profiles" / "DHW_load.csv", index_col="index")
        datetimeindex = pd.date_range(start="2024-01-01", periods=len(cls._profiles), freq=pd.DateOffset(minutes=1))

        cls._profiles = cls._profiles.set_index(datetimeindex, drop=True)

    @classmethod
    def _get_profile(cls, profile_name: Optional[str] = None) -> pd.Series:
        if cls._profiles is None:
            cls._load_profiles_from_file()
        if profile_name is None:
            return cls._profiles[random.choice(cls._profiles.columns)]
        return cls._profiles[profile_name]

    def __init__(self,simulation_period: SimulationPeriod,
                 profile_name: Optional[str] = None) -> None:
        super().__init__("DHWLoad")
        self.simulation_period = simulation_period
        self.profile = self._get_profile(profile_name)

    def dhw_demand(self, timestamp: datetime) -> float:
        """Demand of Domestic Hot Water in Liter"""
        base_year = 2024
        timestamp_ = timestamp - relativedelta(years=timestamp.year - base_year)
        return self.profile.loc[timestamp_]


def test_load() -> None:
    simulation_period = SimulationPeriod(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 31),
        resolution=timedelta(minutes=1)
    )
    load = DHWLoad(
        simulation_period=simulation_period
    )

    powers = np.array([load.dhw_demand(timestamp) for timestamp in simulation_period])
    df = pd.DataFrame(powers, index=simulation_period.datetimeindex())
    print(df.sum())
    import matplotlib.pyplot as plt
    df.plot()
    plt.show()


if __name__ == "__main__":
    test_load()
