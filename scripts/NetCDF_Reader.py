# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 12:39:05 2022

@author: thomitob
"""

""" NetCDF Reader"""

import matplotlib.pyplot as plt
import netCDF4 as nc 
import pandas as pd
import numpy as np; np.random.seed(0)
import seaborn as sns; sns.set_theme()
import numpy as np
import datetime as datetime
import time


########################################################################################################################

#lvl2A plot
# Some old files with depth as dimension
# y1=
# y2=
# y3=
# y4=
# New files with depth_ref as dimension
q1="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2A/L2A_20081002_101438.nc"
q2="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2A/L2A_20100204_093358.nc"
q3="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2A/L2A_20100524_103420.nc"
q4="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2A/L2A_20110106_105931.nc"

ncfile = nc.Dataset(q3)
ncfile.institution 
ncfile.variables["depth"]
ncfile.variables["depth_ref"]
ncfile.variables["Temp"]

#lvl2B plot
# Some old files with depth as dimension
x1="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/old_data/Level2Bx/L2B_20040101_000000.nc" 
x2="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/old_data/Level2Bx/L2B_20080101_000000.nc"
x3="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/old_data/Level2Bx/L2B_20110101_000000.nc"
x4="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/old_data/Level2Bx/L2B_20130101_000000.nc" 
# New files with depth_ref as dimension
z1="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2B/L2B_20090101_000000.nc"
z2="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2B/L2B_20100101_000000.nc"
z3="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2B/L2B_20080101_000000.nc"
z4="C:/Users/thomitob/Documents/git/lake-kivu-ctd-profiles/data/Level2B/L2B_20110101_000000.nc"


ncfile2= nc.Dataset(z4)
ncfile2.variables["depth_ref"]
ncfile2.variables["Temp"]
ncfile2.variables["time"]

##########################################################################################################################

#heatmap - lvl2B
depth_ref2=ncfile2.variables["depth_ref"][:]
depth2 = ncfile2.variables["depth"][:]
temp2 = ncfile2.variables["Temp"][:]
time2=ncfile2.variables["time"][:]
dftime =  pd.DataFrame(time2, 
              columns=['time'])
converted_df = pd.to_datetime(dftime['time'], unit='s')
dftime =  pd.DataFrame(pd.to_datetime(dftime['time'], unit='s'), 
              columns=['time'])

# #plotting depth
# date_format='%Y-%m-%d'
# dfx =  pd.DataFrame(temp2, 
#               columns=converted_df,
#               index=ncfile2.variables["depth"][:])
# dfx.index = np.round(dfx.index, 3)
# dfx.columns = dfx.columns.strftime(date_format) 
# fig, ax = plt.subplots(dpi=150)
# plt.subplots_adjust(bottom=0.3)
# ax = sns.heatmap(dfx,vmin=22, vmax=25, yticklabels=100, cmap="jet")
# ax.set_title("CTD-Heatmap")
# ax.set_xlabel('Date', fontsize=10)
# ax.set_ylabel('Depth [m]', fontsize=10)

#Plotting depth_ref
date_format='%Y-%m-%d'
dfx =  pd.DataFrame(temp2, 
              columns=converted_df,
              index=ncfile2.variables["depth_ref"][:])
dfx.index = np.round(dfx.index, 3)
dfx.columns = dfx.columns.strftime(date_format) 
fig, ax = plt.subplots(dpi=150)
plt.subplots_adjust(bottom=0.3)
ax = sns.heatmap(dfx,vmin=22, vmax=25, yticklabels=1000, cmap="jet")
ax.set_title("CTD-Heatmap")
ax.set_xlabel('Date', fontsize=10)
ax.set_ylabel('Depth_ref [m]', fontsize=10)



##########################################################################################################################

#lvl2A multivariable plot
time = ncfile.variables["time"][:]
depth = -ncfile.variables["depth"][:]
depth_ref= -ncfile.variables["depth_ref"][:]
cond = ncfile.variables["Cond"][:]
temp = ncfile.variables["Temp"][:]
Chl_A = ncfile.variables["Chl_A"][:]
turb= ncfile.variables["Turb"][:]
ph=ncfile.variables["pH"][:]
rho=ncfile.variables["rho"][:]
salin=ncfile.variables["SALIN"][:]
# fig, axs = plt.subplots(3, 2)
fig, axs = plt.subplots(2, 3)


axs[0, 0].plot(cond, depth)
# axs[0, 0].set_title('Conductivity')
axs[0, 0].set(xlabel='Conductivity mS/cm', ylabel='depth (m)')

axs[0, 1].plot(temp, depth, 'tab:orange')
# axs[0, 1].set_title('Temperature')
axs[0, 1].set(xlabel="Temp (degC)", ylabel='depth (m)')

axs[1, 0].plot(Chl_A, depth, 'tab:green')
# axs[1, 0].set_title('chlorophyll A')
axs[1, 0].set(xlabel="chlorophyll A (g/l)", ylabel='depth (m)')

# axs[1, 1].plot(time, depth, 'tab:red')
axs[1, 1].plot(time, depth_ref, 'tab:pink')
# axs[1, 1].set_title('Depth over Time')
axs[1, 1].set(xlabel='time', ylabel='depth (m)')

axs[0, 2].plot(salin, depth_ref, 'tab:purple')
# axs[2, 0].set_title('Turbidity')
axs[0, 2].set(xlabel="salin", ylabel='depth_ref (m)')

# axs[0, 2].plot(turb, depth, 'tab:purple')
# # axs[2, 0].set_title('Turbidity')
# axs[0, 2].set(xlabel="Turbidity (FTU)", ylabel='depth (m)')

axs[1, 2].plot(rho, depth_ref, 'tab:blue')
# axs[2, 1].set_title('pH')
axs[1, 2].set(xlabel="rho", ylabel='depth_ref (m)')


##########################################################################################################################

# #plot offset
offset = depth_ref[50]-depth[50]
# #Timeparser
# datetime.datetime.fromtimestamp(1.2747e+09)
datetime.datetime.utcfromtimestamp(1.2747e+09).strftime('%Y-%m-%d %H:%M:%S')
# pd.to_datetime(1228218997.0, utc=True, origin="unix", unit="s")

##########################################################################################################################



