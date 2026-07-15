from datetime import datetime

from components.prosumer.prosumer import Prosumer


class Bus:
    def __init__(self, prosumers: list[Prosumer]) -> None:
        self.prosumers = prosumers

    def power_kw(self, timestamp: datetime) -> float:
        return sum([
            prosumer.power_kw(timestamp)
            for prosumer in self.prosumers
        ])

