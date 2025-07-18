"""
Usage:
  models_regression.py [--num_cores=<num>]

  -h, --help             Show help text.
  -v, --version          Show version.
  --num_cores=<num>      Number of cores to be used by simulator
"""

from cmath import inf
from re import L, T
from docopt import docopt
import pandas as pd
import numpy as np
import os
from jinja2 import Template
import concurrent.futures
import shutil
from datetime import datetime


def call_simulator(file_name):
    """Call simulation commands to perform simulation.
    Args:
        file_name (str): Netlist file name.
    """
    os.system(f"ngspice -b -a {file_name} -o {file_name}.log > {file_name}.log")


def ext_measured(table, dev_meas):

    # Generate CSVs with truth tables
    df = pd.DataFrame(data=table)
    df.set_index(df.columns[0])
    new_header = df.iloc[0]
    df = df[1:]
    df.columns = new_header
    df.to_csv(dev_meas, index=False)


def ext_simulated(device, processes, volts, temps, dev_netlists, dev_meas, dev_sim):

    # Get all corners simulated
    for process in processes:
        for volt in volts:
            for temp in temps:

                netlist_path = os.path.join(
                    dev_netlists, f"{device}_{process}_{temp}c_{volt}v.spice"
                )
                dev_sim_path = os.path.join(
                    dev_sim, f"{device}_{process}_{temp}c_{volt}v.csv"
                )

                with open(
                    f"device_netlists/gf180mcu_fd_sc_mcu7t5v0__{device}_1.spice"
                ) as f:
                    tmpl = Template(f.read())
                with open(netlist_path, "w") as netlist:
                    netlist.write(
                        tmpl.render(
                            process=process, volt=volt, temp=temp, dev_sim=dev_sim
                        )
                    )

                # Running ngspice for each netlist
                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=workers_count
                ) as executor:
                    executor.submit(call_simulator, netlist_path)

                df_simulated = pd.read_csv(
                    dev_sim_path,
                    header=None,
                    delimiter=r"\s+",
                )
                results = []
                for i in df_simulated.columns:
                    if df_simulated.iloc[0, i] > 2.5:
                        results.append(1)
                    else:
                        results.append(0)
                df_measured = pd.read_csv(dev_meas, header=0)
                df_measured.drop(
                    df_measured.columns[len(df_measured.columns) - 1],
                    axis=1,
                    inplace=True,
                )
                df_measured["output"] = results[1::2]
                df_measured.to_csv(
                    dev_sim_path,
                    index=False,
                )


def error_cal(device, processes, volts, temps, dev_meas, dev_sim):

    print(f"\nSimulation results of {device}")
    measured = pd.read_csv(dev_meas)
    for process in processes:
        for volt in volts:
            for temp in temps:
                dev_sim_path = os.path.join(
                    dev_sim, f"{device}_{process}_{temp}c_{volt}v.csv"
                )
                simulated = pd.read_csv(dev_sim_path)

                res = (measured == simulated).all().all()
                print(
                    "{:^5s} in PVT of {:^7s}, {:^3s}V, {:^3s}C functional simulation = {}".format(
                        device, process, volt, temp, res
                    )
                )
    print(
        "================================================================================================\n"
    )


def main():

    # pandas setup
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("max_colwidth", None)
    pd.set_option("display.width", 1000)

    devices = ["inv", "nand2", "or3"]

    # Generate truth tables data
    inv_table = [["input", "output"], [0, 1], [1, 0]]

    nand2_table = [
        ["input1", "input2", "output"],
        [0, 0, 1],
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ]

    or3_table = [
        ["input1", "input2", "input3", "output"],
        [0, 0, 0, 0],
        [0, 0, 1, 1],
        [0, 1, 0, 1],
        [0, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 1],
    ]

    tables = [inv_table, nand2_table, or3_table]

    processes = ["typical", "ff", "ss"]
    volts = ["5", "4.5", "5.5"]
    temps = ["25", "-40", "125"]

    run_path = datetime.utcnow().strftime("run_std_%Y_%m_%d_%H_%M_%S")
    os.makedirs(run_path, exist_ok=True)

    for i, device in enumerate(devices):
        # Folder structure of simulated values
        dev_meas = os.path.join(run_path, device, f"{device}_measured.csv")
        dev_netlists = os.path.join(run_path, device, f"{device}_netlists")
        dev_sim = os.path.join(run_path, device, "simulated")
        os.makedirs(dev_netlists, exist_ok=True)
        os.makedirs(dev_sim, exist_ok=True)

        # =========== Measure ==============
        ext_measured(tables[i], dev_meas)
        # =========== Simulate ==============
        ext_simulated(device, processes, volts, temps, dev_netlists, dev_meas, dev_sim)

        # ============ Results ==============
        error_cal(device, processes, volts, temps, dev_meas, dev_sim)


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

    # Calling main function
    main()
