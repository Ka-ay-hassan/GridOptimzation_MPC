from datetime import datetime, timedelta

import numpy as np


class Storage:
    pass


class Node:
    def __init__(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon


config = dict(lat=49.123, lon=7.123)

node = Node(**config)


class PV:
    def __init__(self) -> None:
        self._power_data = np.zeros(5)

    def _simulate_one_timestamp(self, timestamp) -> None:
        self._power_data[timestamp] = 0.

    def power_electric_kw(self, timestamp: datetime) -> float:
        """works like a lookup table"""
        if not self._power_data[timestamp]:
            self._simulate_one_timestamp(timestamp)
        return self._power_data[timestamp]


class SimulationPeriod:
    def __init__(self, start: datetime, end: datetime, step_size: timedelta) -> None:
        self.start = start
        self.end = end
        self.step_size = step_size
