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
cm = 1/2.54  # [inches/cm]

data_comb=xr.open_dataset(database_file,decode_times=False)
tnum=data_comb["time"].values
data_comb["time"]=np.array([datetime.utcfromtimestamp(tnum) for tnum in data_comb.time.data])

# Gas data from Bärenbold (2020)
data_gases=pd.read_excel('../../../../../Gases/Gas_profile.xlsx',names=["Depth","CH4avg","CH4std","CO2avg","CO2std"])

# Period to keep
dt_period=[20080101000000,20160101000000]


coltemp=(224/255,196/255,31/255)
colsal=(30/255,178/255,213/255)

print('Data loaded!')

#%% Averaged profile

varnames=["Temp","SALIN","rho"]
prof_avg=[np.nan]*len(varnames)
prof_std=[np.nan]*len(varnames)

hplots=[None]*3

indkeep=np.where(np.logical_and(data_comb["datetime"].data>dt_period[0],data_comb["datetime"].data<dt_period[1]))[0]

for kvar in range(len(varnames)):
    prof_avg[kvar]=np.nanmean(data_comb[varnames[kvar]][:,indkeep],axis=1)
    prof_std[kvar]=np.nanstd(data_comb[varnames[kvar]][:,indkeep],axis=1)
avggrad=(prof_avg[2][1:]-prof_avg[2][:-1])/(data_comb.depth_interp.data[1:]-data_comb.depth_interp.data[:-1])
# remove the opt 10 m
avggrad[data_comb.depth_interp[:-1]<10]=np.nan

# Figure
# fig,ax=plt.subplots(figsize=(3,8))
fig,ax=plt.subplots(1,2,figsize=(12*cm,12*cm),sharey=True)
# fig,ax=plt.subplots(1,2,figsize=(6,8),sharey=True)
hplots[0],=ax[0].plot(prof_avg[0],data_comb.depth_interp,color=coltemp,linewidth=2)
ax[0].spines['bottom'].set_color(coltemp)
ax[0].tick_params(axis='x', colors=coltemp)
axlim=ax[0].get_xlim()
ax[0].set_xticks(ticks=np.arange(22,27,1))
ax[0].set_xlim(axlim)
# Add horizontal lines at selected depths:
ax[0].plot(axlim,[355,355],'--k') # Extraction depth
ax[0].plot(axlim,[240,240],'--k') # Reinjection depth
ax[0].plot(axlim,[data_comb.depth_interp.data[np.nanargmax(avggrad)]]*2,'--k') # Main chemocline

ax2=ax[0].twiny()
hplots[1],=ax2.plot(prof_avg[1],data_comb.depth_interp,color=colsal,linewidth=2)
ax2.spines['bottom'].set_position(('outward', 40))
ax2.spines['bottom'].set_color(colsal)
ax2.xaxis.set_ticks_position("bottom")
ax2.xaxis.set_label_position("bottom")
ax2.tick_params(axis='x', colors=colsal)
ax2lim=ax2.get_xlim()
ax2.set_xticks(ticks=np.arange(1,7))
ax2.set_xlim(ax2lim)

ax3=ax[0].twiny()
hplots[2],=ax3.plot(prof_avg[2],data_comb.depth_interp,'k',linewidth=2)
ax3.set_frame_on(False) # Remove the frame to see the red T axis
ax3lim=ax3.get_xlim()
ax3.set_xticks(ticks=np.arange(995,1005))
ax3.set_xlim(ax3lim)
# ax.fill_betweenx(data_comb_all.depth_interp,rhoprof_avg-rhoprof_std,rhoprof_avg+rhoprof_std,
#                        color='k',alpha=0.2)
ax[0].set_xlabel('Temperature [°C]',color=coltemp)
ax2.set_xlabel('Salinity [g kg$^{-1}$]',color=colsal)
ax3.set_xlabel('Density [kg m$^{-3}$]')
ax[0].set_ylabel('Depth [m]')
ax[0].legend(hplots,["$T$","$S$","$\\rho$"])

# Gas profiles
ax[1].plot(data_gases.CH4avg[~np.isnan(data_gases.CH4avg)],data_gases.Depth[~np.isnan(data_gases.CH4avg)],'.-',markersize=10,color='C2')
ax[1].plot(data_gases.CO2avg[~np.isnan(data_gases.CO2avg)],data_gases.Depth[~np.isnan(data_gases.CO2avg)],'.-',markersize=10,color='C4')
ax[1].set_xticks(ticks=np.arange(0,100,20))
ax[1].set_xlabel('Concentration [mmol L$^{-1}$]')
ax[1].legend(['CH$_4$','CO$_2$'])
ax[0].set_ylim(0,475)
ax[0].invert_yaxis()

fig.set_tight_layout(True)

#%% Save figure

if savefig_bool:
    fig.savefig("../2-Figures_raw/Fig01_raw.png",dpi=400)
    fig.savefig("../2-Figures_raw/Fig01_raw.svg")
    print('Figure saved!')

#%% Close datasets
data_comb.close()
