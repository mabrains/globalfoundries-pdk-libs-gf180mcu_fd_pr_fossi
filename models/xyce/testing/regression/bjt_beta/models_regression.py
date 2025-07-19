"""
Usage:
  models_regression.py [--num_cores=<num>]

  -h, --help             Show help text.
  -v, --version          Show version.
  --num_cores=<num>      Number of cores to be used by simulator
"""

from cmath import inf
from re import T
from docopt import docopt
import pandas as pd
import numpy as np
import os
from jinja2 import Template
import concurrent.futures
import shutil
import logging
import glob
import multiprocessing as mp

pd.options.mode.chained_assignment = None  # default='warn'

PASS_THRESH = 5.0


def check_xyce_version():
    """
    check_xyce_version checks ngspice version and makes sure it would work with the models.
    """
    # ======= Checking Xyce  =======
    Xyce_v_ = os.popen("Xyce  -v 2> /dev/null").read()
    if Xyce_v_ == "":
        logging.error("Xyce is not found. Please make sure Xyce is installed.")
        exit(1)
    elif "7.5" not in Xyce_v_:
        logging.error("Xyce version 7.5 is required.")
        exit(1)


def call_simulator(file_name):
    """Call simulation commands to perform simulation.
    Args:
        file_name (str): Netlist file name.
    """
    os.system(f"Xyce -hspice-ext all {file_name} -l {file_name}.log 2>/dev/null")


def ext_measured(
    dirpath: str,
    device: str,
    vb: str,
    step: list,
    list_devices: list,
    vc: str,
) -> tuple:
    """ext_measured function calculates get measured data

    Args:
        dirpath(str): measured data path
        device(str): npn or pnp
        vb(str): header of first column in the table
        step(str): voltage step
        list_devices(list[str]): name of the devices
        vc(str): column header of the measured sheet
    Returns:
        df(DataFrame): output df
    """
    # Get dimensions used for each device
    dimensions = pd.read_csv(f"{dirpath}/{device}.csv", usecols=["corners"])
    loops = dimensions["corners"].count()
    all_dfs = []
    all_dfs1 = []

    # Extracting measured values for each Device
    for i in range(loops):
        k = i
        if i >= len(list_devices):
            while k >= len(list_devices):
                k = k - len(list_devices)

        # Special case for 1st measured values
        if i == 0:
            if device == "pnp":
                temp_vb = vb
                vb = "-vb "
            # measured Id_sim 0
            col_list = [f"{vb}", f"{vc}{step[0]}", f"{vc}{step[1]}", f"{vc}{step[2]}"]
            df_measured = pd.read_csv(f"{dirpath}/{device}.csv", usecols=col_list)
            df_measured.columns = [
                f"{vb}",
                f"{vc}{step[0]}",
                f"{vc}{step[1]}",
                f"{vc}{step[2]}",
            ]

            if device == "pnp":
                vb = temp_vb

            # measured Id_sim 1
            col_list = [
                f"{vb}",
                f"{vc}{step[0]}.{2 * i + 1}",
                f"{vc}{step[1]}.{2 * i + 1}",
                f"{vc}{step[2]}.{2 * i + 1}",
            ]
            df_measured1 = pd.read_csv(f"{dirpath}/{device}.csv", usecols=col_list)
            df_measured1.columns = [
                f"{vb}",
                f"{vc}{step[0]}",
                f"{vc}{step[1]}",
                f"{vc}{step[2]}",
            ]

        else:
            # measured Id_sim 0
            col_list = [
                f"{vb}",
                f"{vc}{step[0]}.{2 * i}",
                f"{vc}{step[1]}.{2 * i}",
                f"{vc}{step[2]}.{2 * i}",
            ]
            df_measured = pd.read_csv(f"{dirpath}/{device}.csv", usecols=col_list)
            df_measured.columns = [
                f"{vb}",
                f"{vc}{step[0]}",
                f"{vc}{step[1]}",
                f"{vc}{step[2]}",
            ]

            # measured Id_sim 1
            col_list = [
                f"{vb}",
                f"{vc}{step[0]}.{2 * i + 1}",
                f"{vc}{step[1]}.{2 * i + 1}",
                f"{vc}{step[2]}.{2 * i + 1}",
            ]
            df_measured1 = pd.read_csv(f"{dirpath}/{device}.csv", usecols=col_list)
            df_measured1.columns = [
                f"{vb}",
                f"{vc}{step[0]}",
                f"{vc}{step[1]}",
                f"{vc}{step[2]}",
            ]

        all_dfs.append(df_measured)
        all_dfs1.append(df_measured1)
    dfs = pd.concat(all_dfs, axis=1)
    dfs1 = pd.concat(all_dfs1, axis=1)
    dfs.drop_duplicates(inplace=True)
    dfs1.drop_duplicates(inplace=True)
    return dfs, dfs1


def run_sim(
    dirpath: str, device: str, Id_sim: str, list_devices: list, temp: float
) -> dict:
    """Run simulation at specific information and corner
    Args:
        dirpath(str): path to the file where we write data
        device(str): the device instance will be simulated
        Id_sim(str): name of the current
        list_devices(list[str]): name of the devices
        temp(float): a specific temp for simulation


    Returns:
        info(dict): results are stored in,
        and passed to the run_sims function to extract data
    """
    netlist_tmp = f"device_netlists/{device}_{Id_sim}.spice"

    info = {}
    info["device"] = device
    info["temp"] = temp
    info["dev"] = list_devices

    temp_str = temp
    list_devices_str = list_devices

    s = f"{list_devices_str}netlist_t{temp_str}.spice"
    netlist_path = f"{dirpath}/{device}_netlists_{Id_sim}/{s}"
    s = f"t{temp}_simulated_{list_devices_str}.csv"
    result_path = f"{dirpath}/simulated_{Id_sim}/{s}"
    os.makedirs(f"{dirpath}/simulated_{Id_sim}", exist_ok=True)

    with open(netlist_tmp) as f:
        tmpl = Template(f.read())
        os.makedirs(f"{dirpath}/{device}_netlists_{Id_sim}", exist_ok=True)
        with open(netlist_path, "w") as netlist:
            netlist.write(tmpl.render(device=list_devices_str, temp=temp_str))

    # Running ngspice for each netlist
    try:
        call_simulator(netlist_path)

        if os.path.exists(result_path):
            bjt_iv = result_path
        else:
            bjt_iv = "None"

    except Exception:
        bjt_iv = "None"

    info["bjt_beta_simulated"] = bjt_iv

    return info


def run_sims(
    dirpath: str,
    list_devices: list,
    device: str,
    Id_sim: str,
    steps: int,
    num_workers=mp.cpu_count(),
) -> pd.DataFrame:
    """passing netlists to run_sim function
        and storing the results csv files into dataframes

    Args:
        dirpath(str): the path to the file where we write data
        list_devices(list[str]): name of the devices
        device(str): name of the device
        id_rds(str): select id or rds
        steps(int): num of columns in the table
        num_workers=mp.cpu_count() (int): num of cpu used
    Returns:
        df(pd.DataFrame): dataframe contains simulated results
    """
    df1 = pd.read_csv(f"{dirpath}/{device}.csv", usecols=["corners"])
    loops = (df1["corners"]).count()
    temp_range = int(loops / 4)
    df = pd.DataFrame()
    df["dev"] = df1["corners"].dropna()
    df["dev"][0:temp_range] = list_devices
    df["dev"][temp_range : 2 * temp_range] = list_devices
    df["dev"][2 * temp_range : 3 * temp_range] = list_devices
    df["dev"][3 * temp_range : 4 * temp_range] = list_devices
    df["temp"] = 25
    df["temp"][temp_range : 2 * temp_range] = -40
    df["temp"][2 * temp_range : 3 * temp_range] = 125
    df["temp"][3 * temp_range :] = -175

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures_list = []
        for j, row in df.iterrows():
            futures_list.append(
                executor.submit(
                    run_sim,
                    dirpath,
                    device,
                    Id_sim,
                    row["dev"],
                    row["temp"],
                )
            )

        for future in concurrent.futures.as_completed(futures_list):
            try:
                data = future.result()
                results.append(data)
            except Exception as exc:
                logging.info(f"Test case generated an exception: {exc}")
    sf = glob.glob(f"{dirpath}/simulated_{Id_sim}/*.csv")
    # sweeping on all generated cvs files
    for i in range(len(sf)):
        df2 = pd.read_csv(sf[i])
        if device == "npn":
            i_v = "{-I(VCP)}"
            if Id_sim == "Ib":
                i_v = "{-I(VBP)}"
            sdf = df2.pivot(index="V(B)", columns="V(C)", values=i_v)
            sdf.rename(
                columns={1: "vcp1", 2: "vcp2", 3: "vcp3"},
                inplace=True,
            )
        else:
            i_v = "{I(VCP)}"
            if Id_sim == "Ib":
                i_v = "{I(VBP)}"
            sdf = df2.pivot(index="V(B)", columns="V(C)", values=i_v)
            sdf.rename(
                columns={-1: "vcp1", -2: "vcp2", -3: "vcp3"},
                inplace=True,
            )
            # reverse the rows
            sdf = sdf.iloc[::-1]
        sdf.to_csv(sf[i], index=True, header=True, sep=",")
    df1 = pd.DataFrame(results)

    return df


def error_cal(
    sim_df: pd.DataFrame,
    meas_df: pd.DataFrame,
    device: str,
    step: list,
    vc: str,
    Id_sim: str,
    vb: str,
) -> pd.DataFrame:
    """error function calculates the error between measured, simulated data

    Args:

        sim_df(pd.DataFrame): Dataframe contains devices and csv files simulated
        meas_df(pd.DataFrame): Dataframe contains devices and csv files measured
        device(str): The path in which we write data
    Returns:
        df(pd.DataFrame): dataframe contains error results
    """
    merged_dfs = list()
    # create a new dataframe for rms error
    rms_df = pd.DataFrame(columns=["device", "temp", "rms_error"])

    meas_df.to_csv(
        f"bjt_beta_reg/{device}/{device}_measured.csv", index=False, header=True
    )
    meas_df = pd.read_csv(f"bjt_beta_reg/{device}/{device}_measured.csv")
    for i in range(len(sim_df)):
        t = sim_df["temp"].iloc[i]
        dev = sim_df["dev"].iloc[i]
        sim_path = f"bjt_beta_reg/{device}/simulated_{Id_sim}/t{t}_simulated_{dev}.csv"
        simulated_data = pd.read_csv(sim_path)
        if i == 0:
            measured_data = meas_df[
                [f"{vc}{step[0]}", f"{vc}{step[1]}", f"{vc}{step[2]}"]
            ].copy()

            measured_data.rename(
                columns={
                    f"{vc}{step[0]}": "m_vcp1",
                    f"{vc}{step[1]}": "m_vcp2",
                    f"{vc}{step[2]}": "m_vcp3",
                },
                inplace=True,
            )
        else:
            measured_data = meas_df[
                [f"{vc}{step[0]}.{i}", f"{vc}{step[1]}.{i}", f"{vc}{step[2]}.{i}"]
            ].copy()

            measured_data.rename(
                columns={
                    f"{vc}{step[0]}.{i}": "m_vcp1",
                    f"{vc}{step[1]}.{i}": "m_vcp2",
                    f"{vc}{step[2]}.{i}": "m_vcp3",
                },
                inplace=True,
            )
        measured_data[f"{vb}"] = meas_df[f"{vb}"]
        simulated_data[f"{vb}"] = meas_df[f"{vb}"]
        simulated_data["device"] = sim_df["dev"].iloc[i]
        measured_data["device"] = sim_df["dev"].iloc[i]
        simulated_data["temp"] = sim_df["temp"].iloc[i]
        measured_data["temp"] = sim_df["temp"].iloc[i]
        result_data = simulated_data.merge(measured_data, how="left")
        # clipping all the  values to lowest_curr
        lowest_curr = 5e-12
        result_data["vcp1"] = result_data["vcp1"].clip(lower=lowest_curr)
        result_data["vcp2"] = result_data["vcp2"].clip(lower=lowest_curr)
        result_data["vcp3"] = result_data["vcp3"].clip(lower=lowest_curr)
        result_data["m_vcp1"] = result_data["m_vcp1"].clip(lower=lowest_curr)
        result_data["m_vcp2"] = result_data["m_vcp2"].clip(lower=lowest_curr)
        result_data["m_vcp3"] = result_data["m_vcp3"].clip(lower=lowest_curr)

        result_data["step1_error"] = (
            np.abs(result_data["vcp1"] - result_data["m_vcp1"])
            * 100.0
            / (result_data["m_vcp1"])
        )
        result_data["step2_error"] = (
            np.abs(result_data["vcp2"] - result_data["m_vcp2"])
            * 100.0
            / (result_data["m_vcp2"])
        )
        result_data["step3_error"] = (
            np.abs(result_data["vcp3"] - result_data["m_vcp3"])
            * 100.0
            / (result_data["m_vcp3"])
        )
        # fill nan values with 0
        result_data.fillna(0, inplace=True)
        result_data["error"] = (
            np.abs(
                result_data["step1_error"]
                + result_data["step2_error"]
                + result_data["step3_error"]
            )
            / 3
        )
        # get rms error
        result_data["rms_error"] = np.sqrt(np.mean(result_data["error"] ** 2))
        # fill rms dataframe
        rms_df.loc[i] = [
            dev,
            t,
            result_data["rms_error"].iloc[0],
        ]
        merged_dfs.append(result_data)
    merged_out = pd.concat(merged_dfs)
    merged_out.fillna(0, inplace=True)
    merged_out.to_csv(f"bjt_beta_reg/{device}/{Id_sim}_error_analysis.csv", index=False)
    rms_df.to_csv(
        f"bjt_beta_reg/{device}/{Id_sim}_final_error_analysis.csv", index=False
    )
    return rms_df


def main():
    """
    Main function applies all regression steps
    """

    ## Check Xyce version
    check_xyce_version()

    # pandas setup
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("max_colwidth", None)
    pd.set_option("display.width", 1000)

    devices = ["npn", "pnp"]
    list_devices = [
        [
            "npn_10p00x10p00",
            "npn_05p00x05p00",
            "npn_00p54x16p00",
            "npn_00p54x08p00",
            "npn_00p54x04p00",
            "npn_00p54x02p00",
        ],
        ["pnp_10p00x00p42", "pnp_05p00x00p42", "pnp_10p00x10p00", "pnp_05p00x05p00"],
    ]
    vb = ["vbp ", "-vb (V)"]
    vc = ["vcp =", "vc =-"]
    Id_sim = ["Ic", "Ib"]
    step = [1, 2, 3]
    steps = len(step)

    for i, device in enumerate(devices):
        # Folder structure of measured values
        dirpath = f"bjt_beta_reg/{device}"
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        os.makedirs(f"{dirpath}", exist_ok=False)

        read_file = glob.glob(
            f"../../180MCU_SPICE_DATA/BJT/bjt_{device}_beta_f.nl_out.xlsx"
        )
        if len(read_file) < 1:
            logging.info(f"# Can't find data file for device: {device}")
            read_fil = ""
        else:
            read_fil = os.path.abspath(read_file[0])
        logging.info(f"# bjt_beta data points file : {read_fil}")

        if read_fil == "":
            logging.info(
                f"# No datapoints available for validation for device {device}"
            )
            continue
        # From xlsx to csv
        read_file = pd.read_excel(
            f"../../180MCU_SPICE_DATA/BJT/bjt_{device}_beta_f.nl_out.xlsx"
        )
        read_file.to_csv(f"{dirpath}/{device}.csv", index=False, header=True)

        # Folder structure of simulated values
        os.makedirs(f"{dirpath}/simulated_{Id_sim[0]}", exist_ok=False)
        os.makedirs(f"{dirpath}/simulated_{Id_sim[1]}", exist_ok=False)

        # =========== Simulate ==============
        df_ic, df_ib = ext_measured(
            dirpath, device, vb[i], step, list_devices[i], vc[i]
        )
        sims_ic = run_sims(
            dirpath,
            list_devices[i],
            device,
            Id_sim[0],
            steps,
            num_workers=mp.cpu_count(),
        )
        sims_ib = run_sims(
            dirpath,
            list_devices[i],
            device,
            Id_sim[1],
            steps,
            num_workers=mp.cpu_count(),
        )
        merged_all = error_cal(sims_ic, df_ic, device, step, vc[i], Id_sim[0], vb[i])
        merged_all_ib = error_cal(sims_ib, df_ib, device, step, vc[i], Id_sim[1], vb[i])

        # ============ Results =============
        for s in Id_sim:
            if s == Id_sim[1]:
                merged_all = merged_all_ib
            for dev in list_devices[i]:
                min_error_total = float()
                max_error_total = float()
                error_total = float()
                number_of_existance = int()

                # number of rows in the final excel sheet
                num_rows = merged_all["device"].count()

                for n in range(num_rows):
                    if dev == merged_all["device"].iloc[n]:
                        number_of_existance += 1
                        error_total += merged_all["rms_error"].iloc[n]
                        if merged_all["rms_error"].iloc[n] > max_error_total:
                            max_error_total = merged_all["rms_error"].iloc[n]
                        elif merged_all["rms_error"].iloc[n] < min_error_total:
                            min_error_total = merged_all["rms_error"].iloc[n]

                mean_error_total = error_total / number_of_existance

                # Making sure that min, max, mean errors are not > 100%
                if min_error_total > 100:
                    min_error_total = 100

                if max_error_total > 100:
                    max_error_total = 100

                if mean_error_total > 100:
                    mean_error_total = 100

                # logging.infoing min, max, mean errors to the consol
                logging.info(
                    f"# Device {dev} {s} min error: {min_error_total:.2f}, max error: {max_error_total:.2f}, mean error {mean_error_total:.2f}"
                )

                if max_error_total <= PASS_THRESH:
                    logging.info(f"# Device {dev} {s} has passed regression.")
                else:
                    logging.error(
                        f"# Device {dev} {s} has failed regression. Needs more analysis."
                    )


# ================================================================
# -------------------------- MAIN --------------------------------
# ================================================================

if __name__ == "__main__":

    # Args
    arguments = docopt(__doc__, version="comparator: 0.1")
    workers_count = (
        os.cpu_count() * 2
        if arguments["--num_cores"] is None
        else int(arguments["--num_cores"])
    )
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler(),
        ],
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%d-%b-%Y %H:%M:%S",
    )
    # Calling main function
    main()
