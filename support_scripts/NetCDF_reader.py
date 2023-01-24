# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 10:30:13 2022

@author: thomitob
"""
import netCDF4 as nc 
import numpy as np; np.random.seed(0)
import seaborn as sns; sns.set_theme()
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

file="..\data\Level2B\L2B_20081001_000000.nc"
ncfile = nc.Dataset(file)
ncfile.source



# Some Meta Data
try:
    meta_data={ncfile.file_name,
               ncfile.purpose_of_sampling,
               ncfile.latitude,
               ncfile.longitude,
               ncfile.distance_to_GEF,
              }
    pH_calibration=ncfile.pH_calibration

except:
    print("No meta data available")

# lvl2A multivariable plot
time        = ncfile.variables["time"][:].astype(int)
time2       = np.array(time).astype(int)

#depth       = -ncfile.variables["depth"][:]
depth_ref   = -ncfile.variables["depth_ref"][:]
cond        = ncfile.variables["Cond"][:]
temp        = ncfile.variables["Temp"][:]
Chl_A       = ncfile.variables["Chl_A"][:]
turb        = ncfile.variables["Turb"][:]
ph          =ncfile.variables["pH"][:]
rho         =ncfile.variables["rho"][:]
salin       =ncfile.variables["SALIN"][:]


fig, axs    = plt.subplots(2, 3)

indprof=0

axs[0, 0].plot(cond[:,indprof], depth_ref)
axs[0, 0].set(xlabel='Conductivity mS/cm', ylabel='depth_ref (m)')

axs[0, 1].plot(temp[:,indprof], depth_ref, 'tab:orange')
axs[0, 1].set(xlabel="Temp (degC)", ylabel='depth_ref (m)')

axs[1, 0].plot(turb[:,indprof], depth_ref, 'tab:green')
axs[1, 0].set(xlabel="Turbidity (FTU)", ylabel='depth_ref (m)')

# axs[1, 1].plot(time, depth_ref, 'tab:pink')
# axs[1, 1].set(xlabel='time', ylabel='depth_ref (m)')

axs[0, 2].plot(salin[:,indprof], depth_ref, 'tab:purple')
axs[0, 2].set(xlabel="Salinity ('PSU', 'ppt')", ylabel='depth_ref (m)')

axs[1, 2].plot(rho[:,indprof], depth_ref, 'tab:blue')
axs[1, 2].set(xlabel="rho", ylabel='depth_ref (m)')

plt.show() # To display plot in PyCharm