# -*- coding: utf-8 -*-
"""
Plot  averaged profiles and trends of temperature, salinity, density and N2 before and during methane extraction.

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
#%% Parameters

database_file_periods="../../../analysis/3-Periods/database_combined_260m_lake_2periods.nc"
database_file_annual="../../../analysis/3-Periods/database_combined_260m_lake_15periods.nc"
database_file_KW="../../../analysis/3-Periods/database_combined_260m_KW_2periods.nc"
database_file_north="../../../analysis/3-Periods/database_combined_260m_north_2periods.nc"

savefig_bool=True
cm = 1/2.54  # [inches/cm]

data_periods=xr.open_dataset(database_file_periods,decode_times=False)
data_annual=xr.open_dataset(database_file_annual,decode_times=False)
data_KW=xr.open_dataset(database_file_KW,decode_times=False)
data_north=xr.open_dataset(database_file_north,decode_times=False)


datetime_periods=[[datetime.utcfromtimestamp(tnum) for tnum in data_periods.time0_periods.values],
                  [datetime.utcfromtimestamp(tnum) for tnum in data_periods.timef_periods.values]]
z_chem_periods=data_periods.z_chem.values
# z_chem=np.nanmean(z_chem_periods)
z_chem=z_chem_periods[0] # Before methane extraction

time_periods=np.array([data_periods.time0_periods.values,data_periods.timef_periods.values-1])
yearstr_periods=[[str(datetime.utcfromtimestamp(time_periods[0,i]).year) for i in range(len(time_periods[0,:]))],
               [str(datetime.utcfromtimestamp(time_periods[1,i]).year) for i in range(len(time_periods[0,:]))]]


xlim_SALT=[(0.9,5.5),(-0.12,0.12)]
xlim_SALT_zoom=[(2.5,5.5),(-0.12,0.12)]

varnames=["Temp","SALIN","rho","N2"]

layer_depths=[238,278] # Depth of layers used for salt balance (Fig. 3)

print('Data loaded!')

#%% Plot averaged profiles and trends during periods

fig,ax=plt.subplots(2,4,figsize=(18*cm,15*cm),sharey=True)
colval=[(0, 0, 0.8),(0.93,0.5,0)]
# colval=[(0, 0, 0.8),'orange']
colval_trend=colval

hp_all=[]
hp_trend_all=[]
fig_zoom=True
if fig_zoom:
    xlimval_all=[[(23.5,25.5),xlim_SALT_zoom[0],(999.5,1001.5),(-0.5,2.5)],[(-0.07,0.07),xlim_SALT_zoom[1],(-0.07,0.07),(-0.2,0.2)]]
    ylimval=(230,280)
    figname="avgtrend_zoom"
    legloc='upper center'
else:
    xlimval_all=[[(22.7,25.5),xlim_SALT[0],(997.5,1001.5),(-0.5,2.5)],[(-0.12,0.12),xlim_SALT_zoom[1],(-0.05,0.05),(-0.2,0.2)]]
    ylimval=(0,320)
    figname="avgtrend"
    legloc='center right'
    

# Add 2008 profile as a reference:
kprof=0
for kvar in range (len(varnames)):
    exec('profavg=data_annual.meanprof_'+varnames[kvar]+'_avg')
    exec('profstd=data_annual.meanprof_'+varnames[kvar]+'_std')
    if varnames[kvar]=="N2":
        profavg=profavg*1e3
        profstd=profstd*1e3
    hp,=ax[0,kvar].plot(profavg[:,kprof],data_annual.depth_interp,
            color='k')
    if kvar==0:
        hp_all.append(hp)
    ax[0,kvar].fill_betweenx(data_annual.depth_interp, 
                           profavg[:,kprof]-profstd[:,kprof], 
                           profavg[:,kprof]+profstd[:,kprof],
                           color='k',alpha=0.2)


for kprof in np.arange(len(data_periods["time0_periods"])):
    for kvar in range (len(varnames)):
        if kprof==0:
            exec('profavg=data_periods.meanprof_'+varnames[kvar]+'_avg')
            exec('profstd=data_periods.meanprof_'+varnames[kvar]+'_std')
        else:
            exec('profavg=data_KW.meanprof_'+varnames[kvar]+'_avg')
            exec('profstd=data_KW.meanprof_'+varnames[kvar]+'_std')
        if varnames[kvar]=="N2": # Change units
            profavg=profavg*1e3
            profstd=profstd*1e3
    
        # Average profiles
        hp,=ax[0,kvar].plot(profavg[:,kprof],data_periods.depth_interp,
                color=colval[kprof])
        if kvar==0:
            hp_all.append(hp)
        ax[0,kvar].fill_betweenx(data_periods.depth_interp, 
                               profavg[:,kprof]-profstd[:,kprof], 
                               profavg[:,kprof]+profstd[:,kprof],
                               color=colval[kprof],alpha=0.2)
        
        # Trends
        if kprof==0:
            exec('trendavg=data_periods.trendfit_'+varnames[kvar])
            exec('trenderr=data_periods.trenderr_'+varnames[kvar])
        else:
            exec('trendavg=data_KW.trendfit_'+varnames[kvar])
            exec('trenderr=data_KW.trenderr_'+varnames[kvar])
        if varnames[kvar]=="N2":
            trendavg=trendavg*1e3
        hp_trend,=ax[1,kvar].plot(trendavg[:,kprof],data_periods.depth_trend,
                color=colval_trend[kprof])
        if kvar==0:
            hp_trend_all.append(hp_trend)
        ax[1,kvar].fill_betweenx(data_periods.depth_trend, 
                               trendavg[:,kprof]-trenderr[:,kprof], 
                               trendavg[:,kprof]+trenderr[:,kprof],
                               color=colval[kprof],alpha=0.2)

# Add northern profiles
for kvar in range (len(varnames)):
    exec('profavg=data_north.meanprof_'+varnames[kvar]+'_avg')
    exec('profstd=data_north.meanprof_'+varnames[kvar]+'_std')
    if varnames[kvar]=="N2": # Change units
        profavg=profavg*1e3
        profstd=profstd*1e3

    # Average profiles
    hp,=ax[0,kvar].plot(profavg[:,1],data_periods.depth_interp,
            color=[0.8,0,0],linestyle=(0,(1,2)),linewidth=2.5)
    if kvar==0:
        hp_all.append(hp)
    # ax[0,kvar].fill_betweenx(data_periods.depth_interp, 
    #                        profavg[:,1]-profstd[:,1], 
    #                        profavg[:,1]+profstd[:,1],
    #                        color=[0.8,0,0],alpha=0.2)
    
    # Trends
    exec('trendavg=data_north.trendfit_'+varnames[kvar])
    if varnames[kvar]=="N2":
        trendavg=trendavg*1e3
    hp_trend,=ax[1,kvar].plot(trendavg[:,1],data_periods.depth_trend,
            color=[0.8,0,0],linestyle=(0,(1,2)),linewidth=2.5)
    if kvar==0:
        hp_trend_all.append(hp_trend)

 
for k in range(len(varnames)):
    
    ax[1,k].plot([0,0],[0,300],'-k')
    xlimval=xlimval_all[0][k]
    ax[0,k].plot(xlimval,[z_chem,z_chem],'--k')
    ax[0,k].set_xlim(xlimval)
    xlimval=xlimval_all[1][k]
    ax[1,k].plot(xlimval,[z_chem,z_chem],'--k')
    if varnames[k]=="SALIN": # Add layer depths
        for zl in layer_depths:
            ax[1,k].plot(xlimval,[zl]*2,':',color=colval[1])
    ax[1,k].set_xlim(xlimval)


ax[0,0].set_ylim(ylimval)
# ax[0,2].legend(handles=hp_all,labels=['Initial (2008)',
#     'Before extraction ({}-{})'.format(yearstr_periods[0][0],yearstr_periods[1][0]),
#                                      'During extraction, $L_{{\\rm GEP}}<2$ km ({}-{})'.format(yearstr_periods[0][1],yearstr_periods[1][1]),
#                                      'During extraction,  $L_{{\\rm GEP}}>25$ km ({}-{})'.format(yearstr_periods[0][1],yearstr_periods[1][1])],loc=legloc)
ax[0,2].legend(handles=hp_all,labels=['Initial (2008)',
    'Before extraction ({}-{})'.format(yearstr_periods[0][0],yearstr_periods[1][0]),
                                     'During extraction, near Kivuwatt ({}-{})'.format(yearstr_periods[0][1],yearstr_periods[1][1]),
                                     'During extraction,  northern region ({}-{})'.format(yearstr_periods[0][1],yearstr_periods[1][1])],loc=legloc)
ax[0,0].invert_yaxis()
ax[0,0].set_ylabel('Depth [m]')
ax[0,0].set_xlabel('$T$ [°C]')
ax[0,1].set_xlabel('$S$ [g.kg$^{-1}$]')
ax[0,2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')
ax[0,3].set_xlabel('$N^2$ [$10^{-3}$ s$^{-2}$]')

ax[1,0].set_xlabel('d$T$/d$t$\n[°C.yr$^{-1}$]')
# ax[1,0].legend(handles=hp_trend_all,labels=['Before extraction ({}-{})'.format(yearstr_periods[0][0],yearstr_periods[1][0]),
                                     # 'During extraction ({}-{})'.format(yearstr_periods[0][1],yearstr_periods[1][1])],loc=legloc)
ax[1,0].set_ylabel('Depth [m]')
ax[1,1].set_xlabel('d$S$/d$t$\n[g.kg$^{-1}$.yr$^{-1}$]')

ax[1,2].set_xlabel('d$\\rho$/d$t$\n[kg.m$^{-3}$.yr$^{-1}$]')
ax[1,2].set_yticks(ticks=np.arange(ylimval[0],ylimval[1],20))

ax[1,3].set_xlabel('d$N^2$/d$t$\n[$10^{-3}$ s$^{-2}$.yr$^{-1}$]')


# fig.set_tight_layout(True)


#%% Save figure

if savefig_bool:
    fig.savefig("../2-Figures_raw/Fig02_raw.png",dpi=400)
    fig.savefig("../2-Figures_raw/Fig02_raw.svg")
    print('Figure saved!')

#%% Close datasets
data_periods.close()
data_annual.close()
data_KW.close()
data_north.close()
