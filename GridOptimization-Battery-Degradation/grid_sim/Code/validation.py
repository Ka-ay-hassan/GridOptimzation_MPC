import pandas as pd
import math as m
from datetime import datetime, timedelta
from Code.paths import DATA, RESULTS
from input import CONFIG
from matplotlib import pyplot as plt
from matplotlib import dates as mdates

date_format = mdates.DateFormatter('%d.%m.%y')


def plot_single_load(data: pd.DataFrame, load: str) -> None:
    fig, ax = plt.subplots(tight_layout=True, figsize=(6, 2.5))
    ax.plot(data[load], label=load)
    ax.set(xlabel="Zeit", ylabel="$\Delta$ Power / kW", title=load)
    # ax.legend(bbox_to_anchor=(0.5, -0.3), loc="upper center", ncol=2, fontsize=9)
    # ax.set_xticklabels(data.index, rotation=30, ha='right')
    ax.xaxis.set_major_formatter(date_format)
    plt.ylim(top=plt.yticks()[0][-1], bottom=plt.yticks()[0][0])
    plt.xlim(left=plt.xticks()[0][0], right=plt.xticks()[0][-1])
    plt.grid()
    plt.savefig(RESULTS / "plots" / f"validation_timestep_{load}.svg")


def main():
    # simulation time period (should match validation time period)
    start = datetime.strptime(CONFIG["timeperiod"]["start"], '%Y-%m-%d %H:%M')
    end = datetime.strptime(CONFIG["timeperiod"]["end"], '%Y-%m-%d %H:%M')
    resolution = timedelta(minutes=CONFIG["timeperiod"]["resolution_min"])
    year = str(start.year)
    if year == "2023" or year == "2019":
        # data import + shaping data to be the right format for comparison
        df_validation = pd.read_csv(DATA / "validation_data" / ("cv_st_" + year + "_1h.csv"), delimiter=";",
                                    index_col="X", parse_dates=True, decimal=",", date_format="mixed", dayfirst=True)
        df_validation = df_validation.loc[start:(end - resolution), :]
        df_mapping = pd.read_csv(DATA / "validation_data" / "mapping.csv", delimiter=";")
        df_mapping = df_mapping.groupby("load_name")
        df_simulated_data = pd.read_csv(RESULTS / "res_load" / "p_mw.csv", delimiter=";", index_col=0)
        df_simulated_data = df_simulated_data * m.pow(10, 3)  # MW in kW
        df_simulated_data["date_time"] = pd.date_range(start=start, end=(end - resolution), freq=resolution)
        df_simulated_data = df_simulated_data.groupby(pd.Grouper(key="date_time", axis=0, freq='h')).sum() / (
                60 / (resolution.seconds // 60))
        # initializing dataframes
        diff_sim_measured = pd.DataFrame(index=pd.date_range(start=start, end=(end - resolution), freq="1h"))
        diff_yearly_energy = pd.DataFrame(
            0.0, index=list(df_mapping.groups), columns=["validation_data", "simulated_data", "abs_difference"]
        )
        factor_time_period_to_year = timedelta(days=365) / timedelta(days=(end - start).days)
        # calculation of difference between simulated and validation data per timestep and per year
        for ele in df_mapping.groups:
            diff_sim_measured[ele] = 0.0
            diff_sim_measured[ele] += df_simulated_data[str(df_mapping.get_group(ele)["load_index"].values[0])]
            diff_yearly_energy.loc[ele, "simulated_data"] = (
                    df_simulated_data[str(
                        df_mapping.get_group(ele)["load_index"].values[0]
                    )].sum() * factor_time_period_to_year / 1000  # in MWh
            )
            for name_val_data in df_mapping.get_group(ele)["val_data_name"]:
                diff_sim_measured[ele] -= df_validation[name_val_data]
                diff_yearly_energy.loc[ele, "validation_data"] += (
                        df_validation[name_val_data].sum() * factor_time_period_to_year / 1000  # in MWh
                )
        diff_yearly_energy["abs_difference"] = abs(
            diff_yearly_energy["simulated_data"] - diff_yearly_energy["validation_data"]
        )
        rel_diff = diff_yearly_energy["abs_difference"] / diff_yearly_energy[["validation_data", "simulated_data"]].max(
            axis=1)
        # visualisation + data saving
        diff_sim_measured.to_csv(
            RESULTS / "validation" / f"difference_simulated_vs_validation_data_per_timestep_{year}.csv"
        )
        diff_yearly_energy.to_csv(
            RESULTS / "validation" / f"difference_simulated_vs_validation_data_per_year_{year}.csv"
        )
        # plot difference between simulated and measured data per timestep
        fig, ax = plt.subplots(tight_layout=True, figsize=(6, 2.5))
        ax.plot(diff_sim_measured, label=diff_sim_measured.columns)
        ax.set(xlabel="Zeit", ylabel="$\Delta$ Power / kW")
        # ax.legend(bbox_to_anchor=(0.5, -0.3), loc="upper center", ncol=2, fontsize=9)
        ax.set_xticklabels(diff_sim_measured.index, rotation=30, ha='right')
        ax.xaxis.set_major_formatter(date_format)
        plt.ylim(top=plt.yticks()[0][-1], bottom=plt.yticks()[0][0])
        plt.xlim(left=plt.xticks()[0][0], right=plt.xticks()[0][-1])
        plt.grid()
        plt.savefig(RESULTS / "plots" / f"validation_timestep_{year}.svg")
        # plot difference between the energy of simulated and measured loads per year
        fig, ax = plt.subplots(tight_layout=True)
        new_labels = [col.replace("_", " ") for col in diff_yearly_energy.columns]
        print(new_labels)
        new_labels = ["validation data", "simulated data", "absolute difference"]
        ax.plot(diff_yearly_energy, label=new_labels)
        ax.set(ylabel="$\Delta$ Energy / MWh")
        ax.set_xticklabels(diff_yearly_energy.index, rotation=30, ha='right')
        # ax.legend(bbox_to_anchor=(0.5, 1.05), loc="lower center", ncol=1)
        ax.legend()
        plt.grid()
        plt.ylim(top=plt.yticks()[0][-1], bottom=plt.yticks()[0][0])
        plt.xlim(left=plt.xticks()[0][0], right=plt.xticks()[0][-1])
        plt.savefig(RESULTS / "plots" / f"validation_year_{year}.svg")
        # plot relative difference per load
        fig, ax = plt.subplots(tight_layout=True)
        ax.plot(rel_diff)
        ax.set(ylabel="$\Delta$ Energy / MWh")
        ax.set_xticklabels(rel_diff.index, rotation=30, ha='right')
        plt.grid()
        plt.ylim(top=plt.yticks()[0][-1], bottom=plt.yticks()[0][0])
        plt.xlim(left=plt.xticks()[0][0], right=plt.xticks()[0][-1])
        plt.savefig(RESULTS / "plots" / f"validation_year_rel_{year}.svg")
        # plot difference at single problematic loads per timestep
        plot_single_load(data=diff_sim_measured, load="L1 Aero-Gas Institutsgebäude")
        plot_single_load(data=diff_sim_measured, load="Verfahrenstechnik und Dampfkesselwesen")
        plot_single_load(data=diff_sim_measured, load="Verfügungsgebäude")
        plt.show()


if __name__ == "__main__":
    main()
