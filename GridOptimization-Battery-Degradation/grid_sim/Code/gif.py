from functools import partial
from typing import Literal
from pathlib import Path
from matplotlib import dates as m_dates
from shapely.geometry import Point

import geopandas as gp
import contextily as cx
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
import matplotlib.animation as animation

from Code.paths import SHAPEFILES, RESULTS
from Code.input import CONFIG

date_format = m_dates.DateFormatter('%d.%m')


def read_shapefile(file_path: Path) -> gp.geodataframe:
    shapefile = gp.read_file(file_path)
    return shapefile


def load_shapefile_building() -> gp.geodataframe:
    file_path_shapefile_buildings = SHAPEFILES / "buildings/basis-uni-komplett.shp"
    buildings = read_shapefile(file_path_shapefile_buildings)
    return buildings.to_crs("EPSG:4326")


def load_shapefile_grid() -> gp.geodataframe:
    file_path_shapefile_grid = SHAPEFILES / "grid/campus-netz.shp"
    grid_shapefile = read_shapefile(file_path_shapefile_grid)
    return grid_shapefile.set_crs("EPSG:4326")


def merge_frames(gdf: gp.GeoDataFrame, df: pd.DataFrame) -> gp.GeoDataFrame:
    return gdf.merge(df, left_on="geb_id", right_on="building_id")


def find_shape_for_node(gdf: gp.GeoDataFrame, df: pd.DataFrame) -> gp.GeoDataFrame:
    # create shapefile for node coordinates
    coords = [Point(xy) for xy in zip(df["x"], df["y"])]
    nodes = gp.GeoDataFrame(df, crs="EPSG:4326", geometry=coords)
    point_in_shapefile = gp.tools.sjoin(nodes, gdf, how="left")
    return nodes


def plot(
        profile_type: Literal["waerme", "kaelte", "heizung", "strom"],
        label: str, title: str,
        df: pd.DataFrame, time_period: pd.DatetimeIndex
) -> None:
    if 'load' in title:
        gdf = load_shapefile_building()
        gdf = merge_frames(gdf, df)
    elif 'bus' in title:
        gdf = load_shapefile_grid()
        df = find_shape_for_node(gdf, df)
    fig, axes = plt.subplots(2, 2, figsize=(5.2, 4), width_ratios=[20, 1], height_ratios=[20, 1],
                             frameon=False, gridspec_kw={"bottom": 0.07, "top": 0.93, "right": 0.8, "left": 0.05})  # 0.88
    ax = axes[0, 0]
    axes[1, 1].set_axis_off()

    cax = axes[0, 1]
    yax = axes[1, 0]
    yax.set(
        xlim=(time_period[0], time_period[-1]),
        ylim=(0, 1),
        yticks=[],
        # xticks=time_period,
    )
    # ax.set_title(title)
    yax.xaxis.set_major_formatter(date_format)
    cmap = mpl.colormaps["gnuplot"]
    if 'load' in title:
        ax = gdf.plot(
            ax=ax,
            cax=cax,
            cmap=cmap,
            column=time_period[0],
            legend=True,
            legend_kwds={
                "label": "Power / MW",
            },
            vmin=gdf.iloc[:, -(time_period.size + 1):-1].min().min(),
            vmax=gdf.iloc[:, -(time_period.size + 1):-1].max().max(),
            aspect=1
        )
    else:
        ax = df.plot(
            ax=ax,
            cax=cax,
            cmap=cmap,
            column=time_period[0],
            legend=True,
            legend_kwds={
                "label": "Voltage / p.u.",
            },
            vmin=df.iloc[:, -(time_period.size + 3):-3].min().min(),
            vmax=df.iloc[:, -(time_period.size + 3):-3].max().max(),
            s=5,
            aspect=1
        )
    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.CartoDB.Positron)
    txt = ax.texts[-1]
    txt.set_text("")
    ax.set_axis_off()

    intervall = int(int(CONFIG["options"]["animation_intervall_h"]) * 60 / int(time_period.freqstr.split("m")[0]))

    def plot_once(i, ax, yax):
        if 'load' in title:
            ax = gdf.plot(
                ax=ax,
                cax=cax,
                cmap=cmap,
                column=time_period[i*intervall],
                legend=True,
                legend_kwds={
                    "label": "Power / MW",
                },
                vmin=gdf.iloc[:, -(time_period.size + 1):-1].min().min(),
                vmax=gdf.iloc[:, -(time_period.size+1):-1].max().max(),
                aspect=1
            )
        else:
            ax = df.plot(
                ax=ax,
                cax=cax,
                cmap=cmap,
                column=time_period[i * intervall],
                legend=True,
                legend_kwds={
                    "label": "Voltage / p.u.",
                },
                vmin=df.iloc[:, -(time_period.size + 3):-3].min().min(),
                vmax=df.iloc[:, -(time_period.size + 3):-3].max().max(),
                s=5,
                aspect=1
            )
        yax.bar(time_period[i*intervall], 1, width=1, color="grey")
        return ax,

    print("animation loading")
    ani = animation.FuncAnimation(fig, partial(plot_once, ax=ax, yax=yax), repeat=True,
                                  frames=int(time_period.size/intervall), interval=300)

    # To save the animation using Pillow as a gif
    writer = animation.PillowWriter(fps=2,
                                    metadata=dict(artist='Johannes Beck'),
                                    bitrate=1800)
    path = RESULTS / "gif"
    ani.save(path / f'{profile_type}_{title}_{label}.gif', writer=writer, dpi=400)
