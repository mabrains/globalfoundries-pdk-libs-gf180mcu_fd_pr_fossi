# GF180MCU ngspice-models

## Folder Structure

```text
📁 ngspice
 ┣ 📜README.md                      This file to document GF180MCU Models for ngspice simulator.
 ┣ 📜design.spice                   Global Parameter Settings (MonteCarlo, matching simulation settings, Flicker noise setting).
 ┣ 📜sm141064.spice                 Model card for all devices except high voltage.
 ┣ 📜sm141064_mim.spice             Model card for MIMCAP devices loaded in sm141064.ngspice file.
 ┣ 📜smbb000149.spice               High voltage devices model card.
 ┣ 📁testing                        Testing environment directory for GF180MCU ngspice-models.
 ```
