import datetime
from typing import Literal

from utilities.id_name_generator import create_id, create_name


class Prosumer:
    _power_type = None
    POWER_TYPE_MAP = {
        "PV": frozenset(["electrical"]),
        "ChargingPoint": frozenset(["electrical"]),
        "ElectricalLoad": frozenset(["electrical"]),
        "DHWLoad": frozenset(["thermal"]),
        "HeatPump": frozenset(["electrical", "thermal"]),
        "LargeScaleHeatPump": frozenset(["electrical", "thermal"]),
        "HotWaterTank": frozenset(["thermal"]),
        "BatterySystem": frozenset(["electrical"]),
        "Building": frozenset(["thermal"]),
    }

    def __init__(self,
                 prosumer_type_str: Literal[
                     "PV", "ChargingPoint", "ElectricalLoad", "DHWLoad", "HeatPump", "HotWaterTank", "BatterySystem",
                     "Building"]) -> None:
        """
        Initialize a Prosumer object with the given prosumer type.

        Parameters:
            prosumer_type_str (Literal["PV", "HeatPump", "ChargingPoint", "ElectricalLoad", "DHWLoad"]): The type of the prosumer.
        """
        self._id: str = create_id("Prosumer")
        self.name: str = create_name(prosumer_type_str)

        # Set the power type based on the prosumer type
        self._power_type = self.POWER_TYPE_MAP[prosumer_type_str]
        if not self._power_type:
            raise ValueError(f"Invalid prosumer type: {prosumer_type_str}")

    @property
    def id(self) -> str:
        return self._id

    def power_kw(self, timestamp: datetime) -> float:
        raise NotImplementedError("Subclasses should implement this!")
    @property
    def power_type(self) -> str:
        if self._power_type is None:
            raise ValueError("No power type provided.")
        return self._power_type

    def propagate(self, *args, **kwargs) -> None:
        raise NotImplementedError("Subclasses should implement this!")
