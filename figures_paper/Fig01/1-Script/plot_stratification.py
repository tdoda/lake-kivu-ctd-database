# -*- coding: utf-8 -*-
"""
Plot the averaged temperature, salinity, density and gas profiles in Lake Kivu.

@author: T. Doda
"""
import netCDF4
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import path
plt.rcParams.update({'svg.fonttype':'none', 'font.sans-serif':'Arial','font.size': 12}) # "none": to export text as text
import pandas as pd
from datetime import datetime, timezone
import math
import cmocean
import xarray as xr
from scipy.stats.distributions import  t
from scipy.interpolate import interp1d
from geopy import distance
import geopandas as gpd
from shapely.geometry import Point, Polygon
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__),'..', '..','Functions'))
from functions import *
from functions_plot import *


plt.close ('all')
#%% Data files

database_file="../../../analysis/2-Spatial_categories/database_combined_260m_lake.nc"

savefig_bool=True

data_comb=xr.open_dataset(database_file,decode_times=False)
tnum=data_comb["time"].values
data_comb["time"]=np.array([datetime.utcfromtimestamp(tnum) for tnum in data_comb.time.data])

# Gas data from Bärenbold (2020)
data_gases=pd.read_excel('../../../../../Gases/Gas_profile.xlsx',names=["Depth","CH4avg","CH4std","CO2avg","CO2std"])

print('Data loaded!')

#%% Averaged profile

varnames=["Temp","SALIN","rho"]
prof_avg=[np.nan]*len(varnames)
prof_std=[np.nan]*len(varnames)

for kvar in range(len(varnames)):
    
    prof_avg[kvar]=np.nanmean(data_comb[varnames[kvar]],axis=1)
    prof_std[kvar]=np.nanstd(data_comb[varnames[kvar]],axis=1)

# Figure
# fig,ax=plt.subplots(figsize=(3,8))
fig,ax=plt.subplots(1,2,figsize=(6,5),sharey=True)
# fig,ax=plt.subplots(1,2,figsize=(6,8),sharey=True)
ax[0].plot(prof_avg[0],data_comb.depth_interp,color='orange',linewidth=2)
ax[0].spines['bottom'].set_color('orange')
ax[0].tick_params(axis='x', colors='orange')
axlim=ax[0].get_xlim()
ax[0].set_xticks(ticks=np.arange(22,27,0.5))
ax[0].set_xlim(axlim)

ax2=ax[0].twiny()
ax2.plot(prof_avg[1],data_comb.depth_interp,color=(0,0,0.8),linewidth=2)
ax2.spines['bottom'].set_position(('outward', 40))
ax2.spines['bottom'].set_color((0,0,0.8))
ax2.xaxis.set_ticks_position("bottom")
ax2.xaxis.set_label_position("bottom")
ax2.tick_params(axis='x', colors=(0,0,0.8))
ax2lim=ax2.get_xlim()
ax2.set_xticks(ticks=np.arange(1,7))
ax2.set_xlim(ax2lim)

ax3=ax[0].twiny()
ax3.plot(prof_avg[2],data_comb.depth_interp,'k',linewidth=2)
ax3.set_frame_on(False) # Remove the frame to see the red T axis
ax3lim=ax3.get_xlim()
ax3.set_xticks(ticks=np.arange(995,1005))
ax3.set_xlim(ax3lim)
# ax.fill_betweenx(data_comb_all.depth_interp,rhoprof_avg-rhoprof_std,rhoprof_avg+rhoprof_std,
#                        color='k',alpha=0.2)
ax[0].set_xlabel('Temperature [°C]',color="orange")
ax2.set_xlabel('Salinity [g kg$^{-1}$]',color=(0,0,0.8))
ax3.set_xlabel('Density [kg m$^{-3}$]')
ax[0].set_ylabel('Depth [m]')

# Gas profiles
ax[1].plot(data_gases.CH4avg[~np.isnan(data_gases.CH4avg)],data_gases.Depth[~np.isnan(data_gases.CH4avg)],'.-',markersize=10,color='C2')
ax[1].plot(data_gases.CO2avg[~np.isnan(data_gases.CO2avg)],data_gases.Depth[~np.isnan(data_gases.CO2avg)],'.-',markersize=10,color='C4')
ax[1].set_xlabel('Concentration [mmol L$^{-1}$]')
ax[1].legend(['CH$_4$','CO$_2$'])
ax[0].set_ylim(0,475)
ax[0].invert_yaxis()

fig.set_tight_layout(True)

if savefig_bool:
    fig.savefig("../2-Figures_raw/Fig01_raw.png",dpi=400)
    fig.savefig("../2-Figures_raw/Fig01_raw.svg",dpi=400)
    print('Figure saved!')

#%% Close datasets
data_comb.close()
