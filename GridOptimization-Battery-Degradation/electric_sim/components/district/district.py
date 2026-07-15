from __future__ import annotations

import json
from datetime import datetime

from components.infrastructure.energy_hub.energy_hub import EnergyHub
from components.infrastructure.grid.electrical_grid import ElectricalGrid


def load_config() -> dict:
    with open('config.json', 'r') as file:
        return json.load(file)


class District:

    @classmethod
    def from_config(cls, energy_hubs: list[dict], electrical_grid: dict) -> District:
        return cls(
            energy_hubs=[
                EnergyHub.from_config(
                    elements=energy_hub["energy_bus"]["elements"],
                    building=energy_hub["energy_bus"]["building"]
                )
                for energy_hub in energy_hubs
            ],
            electrical_grid=ElectricalGrid.from_config(**electrical_grid)
        )

    def __init__(self, energy_hubs: list[EnergyHub], electrical_grid: ElectricalGrid) -> None:
        self.electrical_grid = electrical_grid
        self.energy_hubs = energy_hubs

    def propagate(self, timestamp: datetime) -> None:
        ...

