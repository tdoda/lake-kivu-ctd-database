# Data included in Level-2A csv files

## Purpose of this README file

This README file provides information on the data included in Level2B csv files in the folders `data/Level2A/REMA`and `data/Level2A/Kivuwatt`. Each csv file corresponds to a CTD profile, with the profiling date indicated in the file name (format "L2A_yyyymdd_xxxxx.csv"). Each column corresponds to a quantity measured by the CTD probe as a function of time.

## Columns of the csv files

<font color='red'>*Note that the order of the column might change in future versions.*\
*More information about the variables will be given in the technical report.*</font>

- `Datetime [yyyymmddHHMMSS]`: date and time displayed as a 14 digits number.
- `time [seconds since 1970-01-01 00:00:00]`: time expressed as the number of seconds since 1970-01-01 00:00:00.
- `Press [dbar]`: pressure.
- `Temp [degC]`: water temperature.
- `Cond [mS/cm]`: in situ, temperature-dependent conductivity.
- `Turb [FTU]`: turbidity.
- `pH [_]`: pH.
- `sat [%]`: percentage of oxygen saturation with respect to atmospheric concentration.
- `DO_mg [mg/l]`: dissolved oxygen concentration.
- `time_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the time data.
- `Press_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the pressure data.
- `Temp_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the temperature data.
- `Cond_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the conductivity data.
- `Turb_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the turbidity data.
- `pH_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the pH data.
- `DO_mg_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the oxygen data.
- `rho [kg/m3]`: water density.
- `depth [m]`: actual depth with respect to the lake surface.
- `depth_ref [m]`: depth with respect to a reference altitude of 1462 m above sea level (corrected for water level changes).
- `SALIN [PSU]`: salinity.
- `sat_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the oxygen saturation data.
- `rho_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the water density data.
- `depth_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the depth data.
- `depth_ref_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the reference depth data.
- `SALIN_qual [0 = nothing to report, 1 = more investigation]`: quality flag for the salinity data.