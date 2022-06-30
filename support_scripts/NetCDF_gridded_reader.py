# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 10:33:56 2022

@author: thomitob
"""
import netCDF4 as nc 
import pandas as pd
import numpy as np; np.random.seed(0)
import seaborn as sns; sns.set_theme()
import numpy as np
from matplotlib import pyplot as plt

#Set path to file
file=""
ncfile= nc.Dataset(file)
ncfile.variables["depth_ref"]
ncfile.variables["Temp"]
ncfile.variables["time"]


#heatmap - lvl2B
depth_ref  = ncfile.variables["depth_ref"][:]
temp       = ncfile.variables["Temp"][:]
time       = ncfile.variables["time"][:]

dftime         = pd.DataFrame(time, columns=['time'])
converted_df   = pd.to_datetime(dftime['time'], unit='s')
dftime         = pd.DataFrame(pd.to_datetime(dftime['time'], unit='s'), columns=['time'])

dfx =  pd.DataFrame(temp, 
              columns=converted_df,
              index=ncfile.variables["depth_ref"][:])
dfx.index = np.round(dfx.index, 3)
date_format='%B %Y'
dfx.columns = dfx.columns.strftime(date_format) 


fig, ax = plt.subplots(dpi=150)
plt.subplots_adjust(bottom=0.3)

ax = sns.heatmap(dfx,vmin=22, vmax=25.5, yticklabels=100, cmap="jet")

ax.set_title("CTD-Heatmap")
ax.set_xlabel('Date', fontsize=10)
ax.set_ylabel('Depth_ref [m]', fontsize=10)

