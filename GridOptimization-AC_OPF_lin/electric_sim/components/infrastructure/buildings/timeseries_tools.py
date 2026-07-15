
import os
import sys
from datetime import timedelta

import matplotlib.pyplot as plt
import pandas as pd


# Todo: compare and merge with https://github.com/building-energy/epw
def read_epw(file):
    """
    Simple function to read EnergyPlus Weather files as DataFrames
    :param file: Path to .epw file
    :return: DataFrame with scrape_weather_sweden heat_pump
    """
    # https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html
    columns = [
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "Data",
        "DryBulb",
        "DewPoint",
        "Humidity",
        "AtmosphPress",
        "ExtraHorIrrad",
        "ExtraDNI",
        "HorInfraredIrrad",
        "GHI",
        "DNI",
        "DHI",
        "GHI_Illum",
        "DNI_Illum",
        "DHI_Illum",
        "Zenith_Illum",
        "WindDirection",
        "WindSpeed",
        "TotalSkyCover",
        "OpaqueSkyCover",
        "Visibility",
        "CloudCeiling",
        "WeatherObs",
        "WeatherCodes",
        "PrecipitableWater",
        "AerosolOptDepth",
        "SnowDepth",
        "LastDaySnow",
        "Albedo",
        "LiquidPrecipitationDepth",
        "Liquid Precipitation Quantity",
    ]
    data = pd.read_csv(file, skiprows=8, header=None)
    data.columns = columns
    data.index = pd.to_datetime(data.iloc[:, :5])
    # heat_pump.drop(labels=['year', 'month', 'day', 'hour', 'minute'], axis=1)
    return data


def adopt_ts_dates(ts, year=2017):
    """
    Function to adopt dates as EP Weather files consist normally of several years
    :param ts: dataframe with scrape_weather_sweden heat_pump
    :param year: year to transform to
    :return: reindexed heat_pump
    """
    delta_year = min(ts.index.year) - year
    ts.index = ts.index - pd.DateOffset(years=delta_year)

    return ts


def calc_dts(ts):
    dts = ts.index[1:] - ts.index[:-1]


def get_weather_data(ewp_file, dt_s, year="2017"):
    """
    loads scrape_weather_sweden heat_pump, resamples and fixes dates
    :param ewp_file:
    :param dt_s:
    :param year:
    :return:
    """
    epw_data = read_epw(ewp_file)
    epw_data = epw_data.drop(labels="Data", axis=1)
    # epw_data = adopt_ts_dates(epw_data, year=year)
    stepsize = epw_data.index[1] - epw_data.index[0]
    epw_data.index = pd.date_range(start=str(year), end=str(int(year) + 1), freq="{:.0f}S".format(stepsize.total_seconds()))[
        : len(epw_data)
    ]
    epw_data["year"] = year
    epw_data = epw_data.resample(rule=timedelta(seconds=dt_s)).interpolate()
    epw_data.index.name = "datetime"

    return epw_data


def test_read_epw():
    """
    Simple tests for read_epw function. Plots scrape_weather_sweden heat_pump
    :return:
    """
    # plot irrad
    asset_path = os.path.dirname(os.path.dirname(__file__))
    file = os.path.join(os.path.dirname(__file__), "..", "heat_pump", "timeseries", "scrape_weather_sweden.epw")
    data = read_epw(file)
    data.loc[:, ["HorInfraredIrrad", "GHI", "DNI", "DHI"]].plot()
    data.loc[:, ["HorInfraredIrrad", "TotalSkyCover", "OpaqueSkyCover"]].plot(secondary_y=["TotalSkyCover", "OpaqueSkyCover"])
    plt.show()


def fix_ts_dates(config):
    """
    adopt date of timeseries and check lengths
    """
    tsdict = config["timeseries"]
    ts_lenght = []
    for ts in tsdict:
        # get ts
        ts_i = tsdict[ts]
        ts_i = ts_i.tz_localize(None)
        if not config["start_date"].is_leap_year:
            ts_i = ts_i[~((ts_i.index.month == 2) & (ts_i.index.day == 29))]
            ts_i.reset_index()

        ts_i = adopt_ts_dates(ts_i, year=config["start_date"].year)
        ts_i = ts_i[config["start_date"] : config["end_date"] + timedelta(days=2)]
        ts_i = ts_i.dropna()
        ts_lenght.append(len(ts_i))
        # save ts to config
        tsdict[ts] = ts_i

    if len(set(ts_lenght)) > 1:
        print("error: Timeseries have different lengths")
        sys.exit()
    config["n_steps_2days"] = len(config["timeseries"][ts])
    config["n_steps"] = len(config["timeseries"][ts]) - round(2*24*3600/config["dt_s"])
    config["timeseries"] = tsdict
    return config


if __name__ == "__main__":
    test_read_epw()
