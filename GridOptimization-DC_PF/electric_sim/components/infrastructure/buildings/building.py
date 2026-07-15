#!/usr/bin/env python3

"""Simulation Model of a Building with EnergyPlus.

This module contains a class representing a simulation model of a building using EnergyPlus.
It encapsulates the properties and behaviors of a building in the context of energy simulation,
such as energy consumption, temperature control, and environmental impact.
The class interacts with the EnergyPlus API to run simulations and generate useful heat_pump for analysis
and decision-making.
"""

from __future__ import annotations

__author__ = "Abdul Azzam"
__copyright__ = "Copyright (C) 2023 Abdul Azzam"
__license__ = "GPL"
__version__ = "0.1"

import datetime
import os
import shutil
import sys
import json
from typing import Literal, Any, Optional

import pandas as pd
from components.prosumer.prosumer import Prosumer
from components.controller.Controller import PIDController
from eppy.modeleditor import IDF
from datetime import datetime, timedelta
from components.infrastructure.buildings.timeseries_tools import get_weather_data
from utilities.simulation_period import SimulationPeriod
from config.config import PROJ_PATH

import matplotlib.pyplot as plt


# from besos import eppy_funcs as ef


class Building(Prosumer):
    """Represents a simulation model of a building using EnergyPlus."""

    def __init__(self, simulation_period: SimulationPeriod, building_type: str, active_cooling: bool = False,
                 activation_fcn=None):
        """Initializes the Building with a configuration JSON file."""
        super().__init__(self.__class__.__name__)

        # Data directory
        data_path = PROJ_PATH / "data" / "building"

        self.simulation_period = simulation_period
        self.building_type = building_type
        self.active_cooling = active_cooling

        # Get base configuration from json-File
        self.activation_fcn = activation_fcn
        self.start_date = pd.to_datetime(self.simulation_period.start)
        self.end_date = pd.to_datetime(self.simulation_period.end)
        self.dt_s = self.simulation_period.resolution_seconds

        # Paths to the database and energyplus heat_pump files
        self.ep_path = os.path.dirname(os.readlink(shutil.which("energyplus")))

        # Data directory
        self.result_path = os.path.join(data_path, "simresults")
        self.idf_file = os.path.join(data_path, "buildings", self.building_type.split("_")[0],
                                     self.building_type + ".idf")
        self.epw_file = os.path.join(data_path, "DEU_Stuttgart.107380_IWEC.epw")
        self.idd_file = os.path.join(self.ep_path, "Energy+.idd")
        self.eplusout = os.path.join(self.result_path, "eplusout")
        self.temp_idf_path = os.path.join(data_path, "buildings", "temp.idf")
        self.weather_df = get_weather_data(self.epw_file, dt_s=self.dt_s,
                                           year=self.start_date.year).copy()

        self.arglist = [
            "-d",
            self.eplusout,
            "-w",
            self.epw_file,
            self.temp_idf_path,
        ]

        sys.path.insert(0, self.ep_path)
        from pyenergyplus.api import EnergyPlusAPI
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        self.zone_name = "Thermal Zone 1"
        self.idd_path = self.idd_file
        self.house_type = self.building_type
        self.weather_df = self.weather_df

        # Storing stuff
        self.df = pd.DataFrame(columns=["OA Temp", "Zone Temp", "Baseboard Power"], index=pd.DatetimeIndex([]))
        self.got_handles = False
        self.T_outdoor_handle = -1
        self.T_indoor_handle = -1
        self.actuator_handle = -1
        self.count = 0
        self.warm_up = True
        self.actuator_value = 0
        self.u = 0

        self.y_outdoor = []
        self.ghi = []
        self.y_zone = []
        self.baseboard_power = []
        self.GHI_list = self.weather_df["GHI"].tolist()

        # Add component type
        self.component_type = 'sink'

        self.p_el = 0.0
        self.p_thermal = 0.0
        self.pid = PIDController(p=0.5, i=0.05, d=0.01, dt=self.dt_s)

    @property
    def actuator_value(self):
        return self._actuator_value

    @actuator_value.setter
    def actuator_value(self, value):
        self._actuator_value = value

    @property
    def T_indoor(self):
        return self._T_indoor

    @T_indoor.setter
    def T_indoor(self, value):
        self._T_indoor = value

    def callback_function(self, state_argument: int) -> None:
        """
        This function is invoked at each timestep during the simulation. It waits for a readiness signal, retrieves
        necessary heat_pump from the EnergyPlus API, calls the activation function if defined,
        and updates the simulation state.

        :param: state_argument (int): The current state of the EnergyPlus simulation.
        """
        if not self.got_handles:
            if not self.api.exchange.api_data_fully_ready(state_argument):
                return
            self.T_outdoor_handle = self.api.exchange.get_variable_handle(
                state_argument, "SITE OUTDOOR AIR DRYBULB TEMPERATURE", "ENVIRONMENT"
            )
            self.T_indoor_handle = self.api.exchange.get_variable_handle(state_argument, "Zone Mean Air Temperature",
                                                                         self.zone_name)
            self.actuator_handle = self.api.exchange.get_actuator_handle(
                state_argument, "ElectricEquipment", "Electricity Rate", "FAKE_HVAC"
            )

            if -1 in [
                self.T_outdoor_handle,
                self.T_indoor_handle,
                self.actuator_handle,
            ]:
                print("***Invalid handles, check spelling and sensor/actuator availability")
                sys.exit(1)
            self.got_handles = True

        # flag for completion of ep warm up phase
        self.warm_up = self.api.exchange.warmup_flag(state_argument)

        # update index and datetime
        self.T_outdoor = self.api.exchange.get_variable_value(state_argument, self.T_outdoor_handle)
        self._T_indoor = self.api.exchange.get_variable_value(state_argument, self.T_indoor_handle)

        # get current sim time
        ep_dayofyear = self.api.exchange.day_of_year(state_argument)
        ep_minuteofday = self.api.exchange.current_time(state_argument) * 60
        self.ep_datetime = datetime(self.start_date.year, 1, 1) + timedelta(days=ep_dayofyear,
                                                                            minutes=ep_minuteofday)

        #self.control()
        self.actuator_value = self.u
        self.api.exchange.set_actuator_value(state_argument, self.actuator_handle, self.actuator_value)
        if not self.warm_up:
            self.handle_activation()
            # Append the current timestep heat_pump to the lists
            self.y_outdoor.append(self.T_outdoor)
            self.y_zone.append(self.T_indoor)
            self.baseboard_power.append(self.actuator_value)


    def propagate(self) -> None:
        """
        :param arglist:
        :return:
        """

        # Update IDF File for correct simulation dates
        self.update_idf(self.idf_file, self.idd_file)

        # define callback and run simulation
        self.api.runtime.callback_begin_system_timestep_before_predictor(self.state, self.callback_function)
        self.api.runtime.run_energyplus(self.state, self.arglist)

    def save_results(self) -> None:
        """Save results"""
        self.df = pd.DataFrame({
            "OA Temp": self.y_outdoor,
            "Zone Temp": self.y_zone,
            "Baseboard Power": self.baseboard_power
        }, index=pd.date_range(start=self.start_date, periods=len(self.y_outdoor), freq=f'{self.dt_s}S'))

        self.df['GHI'] = self.weather_df['GHI'][self.start_date:self.end_date]
        path = os.path.join(self.result_path, f"{self.house_type}_{self.dt_s}.csv")
        self.df.to_csv(path)

    def plot_results(self) -> None:
        """Plot the results stored in the dataframe."""
        plt.figure(figsize=(10, 6))
        plt.plot(self.df["OA Temp"].tolist(), label='Outdoor Air Temperature')
        plt.plot(self.df["Zone Temp"].tolist(), label='Zone Temperature')
        plt.axhline(y=20, color='r', linestyle='-', label='20°C Line')  # This line adds a straight line at 20°
        plt.xlabel('Time')
        plt.ylabel('Temperature (°C)')
        plt.title('Temperature over Time')
        plt.legend()
        plt.show()

    def update_idf(self, idf_path: str, iddfile: str) -> None:
        """
        Modifies the IDF file with the simulation dates
        :return:
        """
        IDF.setiddname(iddfile)
        idf_file = IDF(idf_path)

        # Design Level for Setpoint calculation
        Elec_Equip = idf_file.idfobjects["ElectricEquipment"][0]
        self.Design_Level = Elec_Equip.Design_Level

        # adjust Run Period object in IDF-file
        Run_period = idf_file.idfobjects["RunPeriod"][0]
        start_date_idf = self.start_date
        end_date_idf = self.end_date
        Run_period.Begin_Year = start_date_idf.year
        Run_period.Begin_Month = start_date_idf.month
        Run_period.Begin_Day_of_Month = start_date_idf.day
        Run_period.End_Year = end_date_idf.year
        Run_period.End_Month = end_date_idf.month
        Run_period.End_Day_of_Month = end_date_idf.day
        Run_period.Day_of_Week_for_Start_Day = ""

        # Timestep in IDF-file -> Smaller than 60s is not possible with EnergyPlus
        Timestep = idf_file.idfobjects["Timestep"][0]
        Timestep.Number_of_Timesteps_per_Hour = 3600 / self.dt_s
        # save idf-file before running simulation

        idf_file.save(filename=self.temp_idf_path)

    def handle_activation(self) -> None:
        """Handle activation"""
        if self.activation_fcn is not None:
            self.activation_fcn()

    def control(self):

        self.err = 21.0 - self._T_indoor
        self.u = self.pid.update(self.err, self.u)
        self.u = max(0, min(self.u, 50e3))

if __name__ == "__main__":
    simulation_period = SimulationPeriod(
        start=datetime(2022, 1, 1),
        end=datetime(2022, 12, 31),
        resolution=timedelta(minutes=60)
    )
    building = Building(simulation_period, "EnEV02_C1")
    building.propagate()
    building.save_results()
    building.plot_results()
