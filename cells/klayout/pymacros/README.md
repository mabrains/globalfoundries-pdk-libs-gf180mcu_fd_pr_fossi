# KLayout PCells implementation

You could use those PCells either in 2 ways:

1. Use Ciel built PDK directly from: https://github.com/fossi-foundation/ciel
2. Use the PDK from this primitive library for testing purposes.

## Using PCells from Ciel

Please refer to this documentation on how to install the PDK via ciel: https://github.com/fossi-foundation/ciel/blob/main/Readme.md

Export PDK_ROOT and PDK:

```bash
export PDK_ROOT=~/.ciel && export PDK=gf180mcuD
```

Export KLAYOUT_PATH:

```bash
export KLAYOUT_PATH=$PDK_ROOT/$PDK/libs.tech/klayout
```

Start KLayout in edit mode:

```bash
klayout -e
```

## Using PCells from this repo directly

To use the PDK from this repo directly, you need to do the following:

1. Go to following folder in the repo `cells/klayout` and then run the following command:

```bash
export KLAYOUT_PATH=`pwd`
```

2. (optional step to enable GUI menu for running DRC/LVS) You will need to run the following commands as well from inside `cells/klayout` folder:

```bash
ln -s ../../tech/klayout/gf180mcu.lyt
ln -s ../../tech/klayout/gf180mcu.lyp
```

3. Go to any location where you want to start designing, and open klayout using the following command:

```bash
klayout -e
```

4. Create a new layout for testing.
5. Press on insert instance.
6. Go to the instance menu and select "GF180MCU" library from the library list.
7. Select the search bottom and it will give the list of PCells that is available in the library.
8. Select any cell and it will show the cell.
9. Go to the PCell tap and change the parameters as needed to change the layout of the PCells.

> [!NOTE]
> This project uses an older version of `gdsfactory` to maintain compatibility with custom PCells developed for the GF180MCU PDK. For version details, refer to the [requirements.txt](../../../requirements.txt) file.
