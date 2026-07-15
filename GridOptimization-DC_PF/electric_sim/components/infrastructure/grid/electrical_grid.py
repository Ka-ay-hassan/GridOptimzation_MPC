from __future__ import annotations

from datetime import datetime
from typing import Optional, List

import pandapower as pp

from components.prosumer.charging_point import ChargingPoint
from components.prosumer.electrical_load import ElectricalLoad
from components.prosumer.heat_pump.heat_pump import HeatPump
from components.prosumer.prosumer import Prosumer
from components.prosumer.pv import PV
from components.infrastructure.energy_hub.energy_hub import EnergyHub
from config.config import PROJ_PATH
from output.plots.grid_plots import plot_voltages
from utilities.simulation_period import SimulationPeriod
from utilities.time_related import TimePeriod


class ElectricalGrid:

    @classmethod
    def from_example(cls) -> ElectricalGrid:
        # grid = pp.from_excel(PROJ_PATH / "data" / "grid" / "campus.xlsx")
        grid = pp.networks.simple_four_bus_system()
        return cls(pp_grid=grid)

    @classmethod
    def from_json(cls, name: str = "pfaffenhof") -> ElectricalGrid:
        return cls(pp_grid=pp.from_json(
            PROJ_PATH / "data" / "grid" / f"{name}.json",
        ))

    def __init__(self, *, simulation_period: SimulationPeriod = None, pp_grid: Optional[pp.pandapowerNet] = None,
                 name: Optional[str] = None, **kwargs) -> None:
        self.simulation_period = simulation_period
        self.pp_grid = pp_grid if pp_grid is not None else pp.create_empty_network(**kwargs)
        self.name = name if name else pp_grid.name
        self._energy_hubs: List[EnergyHub] = []

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"ElectricalGrid(grid={self.pp_grid}, name={self.name})"

    def __getattr__(self, attr: str):
        if hasattr(self.pp_grid, attr):
            return getattr(self.pp_grid, attr)
        raise AttributeError(f"ElectricalGrid object has no attribute '{attr}'")

    def add_energy_hub(self, energy_hub: EnergyHub, bus_id: int) -> None:
        self._energy_hubs.append(energy_hub)
        for element in energy_hub.elements:
            if isinstance(element, ElectricalLoad | HeatPump | ChargingPoint):
                pp.create_load(self.pp_grid, bus=bus_id, p_mw=0)
            elif isinstance(element, PV):
                pp.create_sgen(self.pp_grid, bus=bus_id, p_mw=0)
            else:
                raise ValueError(f"Element {element} of type '{type(element)}' is unknown.")

    @property
    def energy_hubs(self) -> List[EnergyHub]:
        return self._energy_hubs

    def update_energy_hubs(self, timestamp: datetime) -> None:
        for energy_hub in self._energy_hubs:
            bus_id = self.pp_grid.load[self.pp_grid.load['name'] == energy_hub.name].index[0]
            total_power = energy_hub.get_total_power(timestamp)
            if total_power >= 0:
                self.pp_grid.load.at[bus_id, 'p_mw'] = total_power / 1000  # Convert kW to MW
                self.pp_grid.sgen.at[bus_id, 'p_mw'] = 0
            else:
                self.pp_grid.load.at[bus_id, 'p_mw'] = 0
                self.pp_grid.sgen.at[bus_id, 'p_mw'] = -total_power / 1000  # Convert kW to MW

    def runpp(self, timestamp: datetime, **kwargs) -> None:
        self.update_energy_hubs(timestamp)
        pp.runpp(self.pp_grid, **kwargs)

    def runpp_timeseries(self, timeperiod: TimePeriod) -> None:
        for timestamp in timeperiod:
            self.runpp(timestamp)

    def propagate_energy_hubs(self) -> None:
        for energy_hub in self._energy_hubs:
            energy_hub.propagate()

def test_electrical_grid():
    # Create an example grid
    grid = ElectricalGrid.from_example()

    # Create energy hubs
    energy_hub1 = EnergyHub(elements=[PV(power_kw=lambda _: 10)], building=Building())
    energy_hub2 = EnergyHub(elements=[ElectricalLoad(power_kw=lambda _: -5)], building=Building())
    energy_hub3 = EnergyHub(elements=[HeatPump(power_kw=lambda _: -15)], building=Building())

    # Add energy hubs to the grid
    grid.add_energy_hub(energy_hub1, bus_id=0)
    grid.add_energy_hub(energy_hub2, bus_id=1)
    grid.add_energy_hub(energy_hub3, bus_id=2)

    # Run a power flow simulation
    grid.runpp(datetime.now())

    # Print the results
    print(grid.res_bus)

    # Plot voltages
    plot_voltages(grid)
