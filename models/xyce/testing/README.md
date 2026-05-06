# Globalfoundries 180nm MCU models-xyce regression

Explains how to run GF180nm models-xyce regression.

The main purpose of the GF180MCU Models-xyce regression is to compare the simulation results generated from the xyce simulation with the measured data provided by the foundry to verify the functionality of the GF180nm MCU model cards.

## Folder Structure

```text
📁testing
 ┣ 📜README.md                                  This file to document GF180MCU xyce-models testing procedure.
 ┣ 📜Makefile                                   To make a full test for GF180MCU xyce-models.
 ┣ 📁sc_regression/gf180mcu_fd_sc_mcu7t5v0      Directory for GF180MCU xyce-models Standard cells regression.
 ┣ 📁regression                                 Directory for GF180MCU xyce-models devices regression.
 ┣ 📁smoke_test                                 Simple inverter design to test xyce-models.
 ┣ 📁180MCU_SPICE_Models                        Measurement data provided by fab used for model calibration.
 ```

## Prerequisites

You need the following set of tools installed to be able to run the regression:

- Python 3.6+
- Xyce 7.5+

We have tested this using the following setup:

- Python 3.9.12
- Xyce 7.5+

## Regression Usage

- To test specific device for GF180nm models-xyce, you could use the following command in the current testing directory:

```bash
make models-<device_name>
```

Example

```bash
make models-RES
```

- To make a full test for GF180nm models-xyce devices, you could use the following command in the current testing directory:

```bash
make models-xyce
```

- You could check allowed targets in the Makefile, using the following command:

```bash
make help
```

## **Models-xyce Outputs**

You could find the regression run results at `models_run_<date>_<time>` in the current directory.

### Folder Structure of regression run results

```text
📁 models_run_<date>_<time>
 ┣ 📜 run_log.log                        Summary of regression run results for GF180MCU Models-xyce.
 ┗ 📁 <device_group>                     Directory for each device group contains all regression results.
    ┣ 📁 device_netlists                 Contains templates for spice netlists used in regression test.
    ┣ 📜 models_regression.py            Main regression script used for Models-xyce for this device.
    ┣ 📜 plotting.ipynb                  jupyter notebook used to plot regression results.
    ┣ 📜 <device_name>                   Output directory per device in each group contains device netlists, logs and analysis.
 ```

Devices will be failed in models regression if the Quantile error between simulation results and measured data exceeds `5%`, You could check `run_log.log` for regression summary.

Refer to [Percentile regression](https://builtin.com/data-science/boxplot) for more details.
