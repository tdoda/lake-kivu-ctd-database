# Data included in Level-3 csv files

## Purpose of this README file

This README file provides information on the data included in Level2B csv files in the folders `data/Level3/REMA`, `data/Level3/Kivuwatt` and `data/Level3/Combined`. Each csv file corresponds to a quantity measured as a function of time (columns) and depth (rows). The data has been linearly depth interpolated to a 0.2 m spaced grid. The first row of each file contains the UTC dates (format yyyy-mm-dd HH:MM:SS+00:00). The first column of each file contains the interpolated depth [m] with respect to a reference altitude of 1462 m above sea level.

## List of quantities exported as csv files

<font color='red'>*Note that the number of quantities exported as csv files might change in future versions.* \
*More information about the variables will be given in the technical report.*</font>

- `Cond20_mS_cm`: conductivity at 20°C [mS/cm].
- `rho_kg_m3`: water density [kg/m<sup>3</sup>].
- `SALIN_PSU`: salinity [g/kg].
- `Temp [degC]`: water temperature [°C].



