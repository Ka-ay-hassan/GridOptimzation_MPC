from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd

import scipy.optimize as opt

from utilities.simulation_period import SimulationPeriod
from components.prosumer.prosumer import Prosumer

try:
    from rainflow import rainflow as rf

    _RAINFLOW_LOADED = True
except ModuleNotFoundError:
    _RAINFLOW_LOADED = False

try:
    from components.controller.Controller import PIDController

    _PIDController_LOADED = True
except ModuleNotFoundError:
    _PIDController_LOADED = False


@dataclass
class Inverter:
    power_nom_kw: float
    power_min_kw: float = 0


class BatterySystem(Prosumer):  # todo: or just Battery?
    def __init__(
            self,
            capacity_nom_kwh: float,
            power_nom_kw: float,
            simulation_period: SimulationPeriod,
            soc_initial: float = 0.5,
            soh_initial: float = 1.
    ) -> None:
        super().__init__(self.__class__.__name__)
        self.capacity_nom_kwh = capacity_nom_kwh
        self.power_nom_kw = power_nom_kw
        self.simulation_period = simulation_period
        self.soc_initial = soc_initial
        self.soc = soc_initial
        self.soh_initial = soh_initial
        self.soh = soh_initial
        self.data = self._initialize_data()
        # todo: the following must be changed according to the usage
        self.inverter = Inverter(power_nom_kw=power_nom_kw)
        if _PIDController_LOADED:
            pid = [1, 1, 1]
            self.controller = PIDController(*pid, dt=self.simulation_period.dt)

    def _initialize_data(self) -> pd.DataFrame:
        data = pd.DataFrame(
            0,
            index=self.simulation_period.datetimeindex(),
            columns=["power_kw", "soc", "soh"]
        )
        data.loc[:, "soc"] = self.soc_initial
        data.loc[:, "soh"] = self.soh
        return data

    def _update_soc(self, power_kw: float, timestamp: datetime) -> None:
        if power_kw < 0:
            delta_soc = power_kw * self.simulation_period.resolution_hours / self.eta(power_kw) / self.capacity_nom_kwh
        else:
            delta_soc = power_kw * self.simulation_period.resolution_hours * self.eta(power_kw) / self.capacity_nom_kwh
        self.soc += delta_soc
        self.data.loc[timestamp:, "soc"] = self.soc

    def calc_max_power_kw(self):

        if self.soc >= 1.:
            return 0

        energy_not_in_battery_kwh = (1 - self.soc) * self.capacity_nom_kwh
        max_energy_chargeable_kwh = self.power_nom_kw * self.simulation_period.resolution_hours
        if energy_not_in_battery_kwh / max_energy_chargeable_kwh > 1:
            return self.power_nom_kw

        def f(power_kw) -> float:
            """
            condition: p * eta * dt = (1 - soc) * c_nom
            """
            left = power_kw * self.eta(power_kw) * self.simulation_period.resolution_hours
            right = (1 - self.soc) * self.capacity_nom_kwh
            return left - right

        return min(
            opt.newton(f, self.power_nom_kw),
            self.power_nom_kw
        )

    def calc_min_power_kw(self) -> float:

        if self.soc <= 0:
            return 0

        energy_in_battery_kwh = self.soc * self.capacity_nom_kwh
        max_energy_dischargeable_kwh = self.power_nom_kw * self.simulation_period.resolution_hours
        if energy_in_battery_kwh / max_energy_dischargeable_kwh > 1:
            return -self.power_nom_kw

        def f(power_kw) -> float:
            """
            condition: p / eta * dt = (0 - soc) * c_nom
            """
            left = power_kw / self.eta(power_kw) * self.simulation_period.resolution_hours
            right = (0 - self.soc) * self.capacity_nom_kwh
            return left - right

        return max(
            opt.newton(f, -self.power_nom_kw),
            -self.power_nom_kw
        )

    def _filtered_power(self, power_desired_kw: float) -> float:
        """filtering powers that are not possible at the current state of the battery"""
        if power_desired_kw < 0:
            min_power_kw = self.calc_min_power_kw()
            return max(min_power_kw, power_desired_kw)
        max_power_kw = self.calc_max_power_kw()
        return min(max_power_kw, power_desired_kw)

    def set_power_kw(self, power_desired_kw: float, timestamp: datetime) -> float:
        """
        setting the power of the battery
        :param power_desired_kw: desired power to be set (positive for charging, negative for discharging)
        :param timestamp: timestamp at which the power should be set
        :return: actual power of the battery
        """
        power_kw = self._filtered_power(power_desired_kw)
        self._update_soc(power_kw, timestamp)
        self.data.at[timestamp, "power_kw"] = power_kw
        if _RAINFLOW_LOADED:
            self.calc_aging(timestamp)
        return power_kw

    def calc_aging(self, timestamp: datetime):
        """
        calculates the battery ageing according to the jossen paper
        :param soc: soc history of the battery. range: [0,1]
        :param dt: delta t of the battery [s]
        :return: State of health [SOH], calendaric ageing [A_cal], cyclic ageing [A_cyc]
        """
        # calendaric ageing
        hist_height, bin_edge = np.histogram(self.data["soc"].values)
        soc_mean = (bin_edge[1:] - bin_edge[:-1]) / 2 + bin_edge[:-1]  # mean bin values as soc
        dwell_time = self.simulation_period.dt * hist_height
        a_cal = cal_aging(soc_mean=soc_mean, dwell_time=dwell_time)

        # cyclic ageing
        peak_df, count_df = rf.run_rainflow(self.soc, plot=True)  # todo: fix rainflow
        dod = count_df.bin_mean.values
        equ_cycle = count_df["count"].values
        a_cyc = cyc_aging(dod, equ_cycle)

        # update SOH
        self.soh = self.soh_initial - (a_cal + a_cyc)
        self.data.at[timestamp, "soh"] = self.soh

    def eta(self, power_kw: float):
        eta_0 = 0.95  # initial cycling eff
        d = 1 - eta_0  # inital cycling loss
        # c rate
        c = abs(power_kw) / self.capacity_nom_kwh  # c-rate
        return 1 - 0.5 * (c * d * (1 + self.soh))

    def voltage_v(self) -> float:
        """
        Very simple cell voltage estimation, could be improved with
        https://github.com/christiansiegel/electrical-circuit-battery-model
        # linear voltage dependency of the soc
        """
        v_ocv_0 = 3.3  # open circut voltage of cell at soc 0
        dv_dsoc = 0.007  # voltage sensitivity (linear)
        return v_ocv_0 + dv_dsoc * self.soc


def cal_aging(soc_mean: float, dwell_time: timedelta):
    # todo: Add temperature dependency
    # Constants:
    a0 = 3.171e-9  # temp value [1/s]
    b = 0.1447
    soc_ref = 0.5  # reference soc
    # calc ageing
    a_cal = a0 * np.exp(0.007 * (soc_mean - soc_ref) / b) * dwell_time.total_seconds()
    return a_cal
    # try:
    #     return sum(a_cal)
    # except TypeError:
    #     return a_cal


def cyc_aging(dod: np.ndarray, equ_cycle_count: np.ndarray):
    # Constants:
    beta = (
        -2.150677e-6,
        4.843667e-7,
        -1.362036e-8,
        4.649122e-10
    )
    a_cyc = max(
        (beta[3] * dod ** 3 + beta[2] * dod ** 2 + beta[1] * dod + beta[0]) * equ_cycle_count,
        0
    )  # minimum 0

    return a_cyc
    # try:
    #     return sum(a_cyc)
    # except TypeError:
    #     return a_cyc
