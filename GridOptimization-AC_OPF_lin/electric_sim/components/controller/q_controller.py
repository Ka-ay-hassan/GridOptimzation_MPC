"""
All values are taken from VDE-AR-N-4105 (Low Voltage)
"""
import numbers
import typing
from typing import Literal, Optional
import math

import numpy as np

_controller_types = Literal["Q(U)", "cos(phi)(P)", "Q(P)", "const_cos_phi", "all"]
VALID_CONTROLLER_TYPES = typing.get_args(_controller_types)


def _sin_phi(cos_phi: float) -> float:
    phi = math.acos(cos_phi)
    return math.sin(phi)


class _QController:
    def __init__(self, p_nom_kw: float, activation_point: float, q_max_point: float,
                 cos_phi: Optional[float] = None) -> None:
        self.p_nom_kw = p_nom_kw
        self.cos_phi_min = cos_phi if cos_phi is not None else self._cos_phi_min()
        self.sin_phi_max = _sin_phi(self.cos_phi_min)
        self.s_nom_kva = self._s_nom_kva()
        self.q_nom_kvar = self._q_max()
        self.activation_point = activation_point
        self.q_max_point = q_max_point
        self._m = self._create_m()

    def _create_m(self) -> float:
        """creates the slope m of the linear equation y = m * x"""
        if not 0 <= self.activation_point < 1:
            raise ValueError(f"{self.activation_point = } must be in [0,1)")
        if not 0 < self.q_max_point <= 1:
            raise ValueError(f"{self.q_max_point = } must be in (0,1]")
        if not self.activation_point < self.q_max_point:
            raise ValueError(f"{self.activation_point = } must be smaller than {self.q_max_point = }")
        return 1 / (self.q_max_point - self.activation_point)

    def _cos_phi_min(self) -> float:
        """according to VDE-AR-4105"""
        return 0.95 if self.p_nom_kw <= 4.6 else 0.9

    def _s_nom_kva(self) -> float:
        return self.p_nom_kw / self.cos_phi_min

    def _q_max(self) -> float:
        return self.sin_phi_max * self.s_nom_kva


class CosPhiOfP(_QController):
    def __init__(self, p_nom_kw: float, p_rel_activation: float = 0.5,
                 p_rel_max_q: float = 1, cos_phi_min: Optional[float] = None) -> None:
        """
        p_rel_activation = 0.5 (default) -> default from VDE-AR-4105
        p_rel_activation = 0 -> const. cos_phi controller
        p_rel_q_max: p_rel (between 0 and 1) at which the maximum q is provided
        """
        super().__init__(p_nom_kw, p_rel_activation, p_rel_max_q, cos_phi_min)
        self.p_rel_activation = p_rel_activation
        self.p_rel_max_q = p_rel_max_q

    def reactive_power_relative(self, p_kw: float | typing.Sequence[float]) -> float | np.ndarray:
        """
        :param p_kw: active power in kilowatt or Sequence of active power in kilowatt
            positive for load, negative for generator
        :return: reactive power / nominal reactive power
            in consumer counting arrow system
            positive: under-excited
            negative: over-excited
        """
        if not isinstance(p_kw, numbers.Number):
            return np.array([self.reactive_power_relative(p) for p in p_kw])
        if abs(p_kw) > self.p_nom_kw:
            raise ValueError(f"{round(p_kw, 1) = } is greater than nominal power {round(self.p_nom_kw, 1) = }")
        p_rel = p_kw / self.p_nom_kw
        if abs(p_rel) <= self.p_rel_activation:
            return 0.
        signum = 1 if p_kw < 0 else -1
        return signum * (abs(p_rel) - self.p_rel_activation) * self._m

    def reactive_power_kvar(self, p_kw: float | typing.Sequence[float]) -> float | np.ndarray:
        """
        :param p_kw: active power in kilowatt or Sequence of active power in kilowatt
            positive for load, negative for generator
        :return: reactive power in kilovolt-ampere
            in consumer counting arrow system
            positive: under-excited
            negative: over-excited
        """
        if not isinstance(p_kw, numbers.Number):
            return np.array([self.reactive_power_kvar(p) for p in p_kw])
        return self.reactive_power_relative(p_kw) * self.q_nom_kvar


class ConstCosPhi(CosPhiOfP):
    def __init__(self, p_nom_kw: float, cos_phi: Optional[float] = None) -> None:
        super().__init__(p_nom_kw, p_rel_activation=0, p_rel_max_q=1, cos_phi_min=cos_phi)


QOfP = ConstCosPhi


class QOfU(_QController):
    """
    Q(U) = m * U +- c
    """

    def __init__(self, p_nom_kw: float, delta_u_activation: float = 0.03,
                 delta_u_q_max: float = 0.07, cos_phi: Optional[float] = None, ) -> None:
        super().__init__(p_nom_kw, delta_u_activation, delta_u_q_max, cos_phi)
        self.delta_u_activation = delta_u_activation
        self.delta_u_q_max = delta_u_q_max

    def reactive_power_relative(self, voltage_pu: float | typing.Sequence[float]) -> float | np.ndarray:
        """
        :param voltage_pu: voltage in per unit or sequence of voltages in per unit
        :return: reactive power / nominal reactive power
            in consumer counting arrow system
            positive: under-excited
            negative: over-excited
        """
        if not isinstance(voltage_pu, numbers.Number):
            return np.array([self.reactive_power_relative(v) for v in voltage_pu])
        delta_u = voltage_pu - 1.
        if self.delta_u_q_max < delta_u:
            return 1.
        if delta_u < - self.delta_u_q_max:
            return -1.
        if abs(delta_u) <= self.delta_u_activation:
            return 0.
        signum = 1 if 1 < voltage_pu else -1
        return signum * (abs(delta_u) - self.delta_u_activation) * self._m

    def reactive_power_kvar(self, voltage_pu: float | typing.Sequence[float]) -> float | np.ndarray:
        """
        :param voltage_pu: voltage in per unit sequence of voltages in per unit
        :return: reactive power in kilovolt-ampere
            in consumer counting arrow system
            positive: under-excited
            negative: over-excited
        """
        if not isinstance(voltage_pu, numbers.Number):
            return np.array([self.reactive_power_kvar(v) for v in voltage_pu])
        return self.reactive_power_relative(voltage_pu) * self.q_nom_kvar
