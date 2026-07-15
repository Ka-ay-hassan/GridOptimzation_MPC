import os

import matplotlib.pyplot as plt
import matplotlib.dates as m_dates
from datetime import datetime as dt
from datetime import timedelta as td
import pandas as pd
import pandapower as pp

from Code.paths import RESULTS
from Code.input import CONFIG

date_format = m_dates.DateFormatter('%d.%m.%y')


def plt_results_timeseries(net: pp.pandapowerNet) -> None:
    # time period
    date_range = pd.date_range(start=dt.strptime(CONFIG["timeperiod"]["start"], '%Y-%m-%d %H:%M'),
                               end=(dt.strptime(CONFIG["timeperiod"]["end"], '%Y-%m-%d %H:%M') - td(
                                   minutes=CONFIG["timeperiod"]["resolution_min"])),
                               freq=td(minutes=CONFIG["timeperiod"]["resolution_min"]))

    # voltage results
    vm_pu_file = RESULTS / "res_bus" / "vm_pu.csv"
    ax = create_plot(data_file=vm_pu_file, date_range=date_range, net=net, element_type="bus")
    ax.set(
        ylabel="Voltage / p.u."
    )
    plot_settings(ax, n_col_legend=7)
    plt.savefig(RESULTS / "plots" / "busses_vm_pu.svg")

    # line loading results
    ll_file = RESULTS / "res_line" / "loading_percent.csv"
    ax = create_plot(data_file=ll_file, date_range=date_range, net=net, element_type="line")
    ax.set(
        ylabel="Line loading / %",
        ylim=(0, 70)
    )
    plot_settings(ax, n_col_legend=5)
    plt.savefig(RESULTS / "plots" / "lines_loading_percent.svg")

    # load results
    load_file = RESULTS / "res_load" / "p_mw.csv"
    ax = create_plot(data_file=load_file, date_range=date_range, net=net, element_type="load")
    ax.set(
        ylabel="Power / MW",
        ylim=(0, 8)
    )
    plot_settings(ax, n_col_legend=3)
    plt.savefig(RESULTS / "plots" / "loads_p_mw.svg")

    plt.show()


def create_plot(
        data_file: os.PathLike, date_range: pd.DatetimeIndex, net: pp.pandapowerNet, element_type: str
) -> plt.Axes:
    fig, ax = plt.subplots(tight_layout=True, figsize=(6, 2.5))
    data = pd.read_csv(data_file, index_col=0, delimiter=";")
    data.set_index(date_range, drop=True, inplace=True)
    if element_type == "bus":
        data.columns = net.bus.name.values
    elif element_type == "line":
        data.columns = net.line.name.values
    elif element_type == "load":
        data.columns = net.load.name.values
    ax.plot(data, label=data.columns)
    return ax


def plot_settings(ax: plt.Axes, n_col_legend: int) -> None:
    plt.ylim(top=plt.yticks()[0][-1], bottom=plt.yticks()[0][0])
    plt.xlim(left=plt.xticks()[0][0], right=plt.xticks()[0][-1])
    # plt.xlabel("Time / d")
    plt.grid()
    ax.xaxis.set_major_formatter(date_format)
    # ax.legend(bbox_to_anchor=(0.5, -0.2), loc="upper center", ncol=n_col_legend, fontsize="5")
