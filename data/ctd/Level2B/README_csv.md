# Data included in Level-2B csv files

## Purpose of this README file

This README file provides information on the data included in Level2B csv files in the folders `data/Level2B/REMA`and `data/Level2B/Kivuwatt`. Each csv file corresponds to a CTD profile, with the profiling date indicated in the file name (format "L2B_yyyymdd_xxxxx.csv"). Each column corresponds to a quantity measured by the CTD probe as a function of depth, interpolated to a 0.2 m spaced grid.

## Columns of the csv files

<font color='red'>*Note that the order of the column might change in future versions.*\
*More information about the variables will be given in the technical report.*</font>

- `depth_interp [m]`: interpolated depth, with respect to a reference altitude of 1462 m above sea level.
- `Press [dbar]`: pressure.
- `depth [m]`: actual depth with respect to the lake surface.
- `depth_ref [m]`: like `depth_interp [m]` <font color='red'>*(will be removed in future versions)*</font>.
- `Temp [degC]`: water temperature.
- `Cond [mS/cm]`: in situ, temperature-dependent conductivity.
- `Turb [FTU]`: turbidity.
- `pH [_]`: pH.
- `sat [%]`: percentage of oxygen saturation with respect to atmospheric concentration.
- `DO_mg [mg/l]`: dissolved oxygen concentration.
- `rho [kg/m3]`: water density.
- `pt [degC]`: potential water temperature.
- `prho [kg/m3]`: potential water density.
- `SALIN [PSU]`: salinity.
- `Cond20 [mS/cm]`: conductivity at 20°C.

