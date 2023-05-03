# -*- coding: utf-8 -*-
"""
Create a database from grid of profiles

@author: T. Doda
"""
import netCDF4
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timezone
import math
import cmocean
import xarray as xr
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *

plt.close ('all')
#%% Data files

database_files=["database_gov_250m.nc","database_Kivuwatt_250m.nc","database_combined_250m.nc","database_combined_250m_periods.nc","database_combined_0m.nc"]

# nc_gov = netCDF4.Dataset(database_files[0], mode='r', format='NETCDF4_CLASSIC')
# nc_KW = netCDF4.Dataset(database_files[1], mode='r', format='NETCDF4_CLASSIC')
# nc_comb=netCDF4.Dataset(database_files[2], mode='r', format='NETCDF4_CLASSIC')
# nc_gov.close()
# nc_KW.close()
# nc_comb.close()

#data_gov=xr.open_dataset(database_files[0])
# data_KW=xr.open_dataset(database_files[1])
data_comb=xr.open_dataset(database_files[2])
data_comb_periods=xr.open_dataset(database_files[3],decode_times=False)
data_comb_all=xr.open_dataset(database_files[4])
print('Data loaded!')

#%% Plot grid
fig,ax = plt.subplots(3,1,figsize=(8,8),sharex=True,sharey=True)
x,y = np.meshgrid(data_comb.time, data_comb.depth_interp)

c1 = ax[0].pcolormesh(x,y,data_comb.Temp,cmap=cmocean.cm.thermal)
ylimval=ax[0].get_ylim()
for kprof in np.arange(len(data_comb.time)):
            ax[0].plot(np.full(2,data_comb.time[kprof]),np.array([ylimval[1]-10,ylimval[1]]),'-k',linewidth=0.2)
cb1=fig.colorbar(c1, ax=ax[0])
cb1.set_label('Temperature [°c]')
ax[0].set_ylabel('Depth [m]')

c2 = ax[1].pcolormesh(x,y,data_comb.Cond,cmap=cmocean.cm.haline)
cb2=fig.colorbar(c2, ax=ax[1])
cb2.set_label('Conductivity [mS.cm$^{-1}$]')
ax[1].set_ylabel('Depth [m]')

c3 = ax[2].pcolormesh(x,y,data_comb.rho,cmap=cmocean.cm.dense,vmin=998,vmax=1001)
zchem=data_comb.z_maxdens.copy()
zchem[data_comb.z_maxdens<200]=np.nan
ax[2].plot(data_comb.time,zchem,'-r')
ax[2].invert_yaxis()
cb3=fig.colorbar(c3, ax=ax[2])
cb3.set_label('$\\rho$ [kg.m$^{-3}$]')
ax[2].set_ylabel('Depth [m]')
ax[2].tick_params(axis='x',labelrotation=45)

fig.savefig("Figures/timeseries_grid.png",dpi=400)

#%% Plot all profiles

fig,ax=plt.subplots(1,3,figsize=(10,5),sharey=True)
colval=plt.get_cmap('viridis',len(data_comb_all["time"]))
colval2=[(0, 0, 0.8),(0,0.8,0)]
for kprof in np.arange(len(data_comb_all["time"])):
    print('Progress: {:.1f} %'.format(kprof/len(data_comb_all["time"])*100))
    
    ax[0].plot(data_comb_all.Temp[:,kprof],data_comb_all.depth_interp,
            color=colval(kprof))
    
    ax[1].plot(data_comb_all.Cond[:,kprof],data_comb_all.depth_interp,
            color=colval(kprof))
    
    ax[2].plot(data_comb_all.rho[:,kprof],data_comb_all.depth_interp,
            color=colval(kprof))
    # ax[2].plot(data_comb_all.rho[:,kprof],data_comb_all.depth_interp,
    #          color=colval2[int(data_comb_all.data_type[kprof])])

ax[0].invert_yaxis()
ax[0].set_ylabel('Depth [m]')
ax[0].set_xlabel('Temp [°C]')
#ax[1].legend(handles=[hplots_all[i] for i in  indselect],labels=[date_prof[i].year for i in  indselect],fontsize=8,loc='upper right')
ax[1].set_xlabel('Cond [mS.cm$^{-1}$]')
ax[2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')

fig.savefig("Figures/all_profiles.png",dpi=400) 
#%% Plot deep profiles

fig,ax=plt.subplots(1,3,figsize=(10,5),sharey=True)
colval=plt.get_cmap('viridis',len(data_comb["time"]))
colval2=[(0, 0, 0.8),(0,0.8,0)]
for kprof in np.arange(len(data_comb["time"])):
    print('Progress: {:.1f} %'.format(kprof/len(data_comb["time"])*100))
    
    ax[0].plot(data_comb.Temp[:,kprof],data_comb.depth_interp,
            color=colval(kprof))
    
    ax[1].plot(data_comb.Cond[:,kprof],data_comb.depth_interp,
            color=colval(kprof))
    
    ax[2].plot(data_comb.rho[:,kprof],data_comb.depth_interp,
            color=colval(kprof))
    # ax[2].plot(data_comb.rho[:,kprof],data_comb.depth_interp,
    #          color=colval2[int(data_comb.data_type[kprof])])

ax[0].invert_yaxis()
ax[0].set_ylabel('Depth [m]')
ax[0].set_xlabel('Temp [°C]')
#ax[1].legend(handles=[hplots_all[i] for i in  indselect],labels=[date_prof[i].year for i in  indselect],fontsize=8,loc='upper right')
ax[1].set_xlabel('Cond [mS.cm$^{-1}$]')
ax[2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')

fig.savefig("Figures/all_deep_profiles.png",dpi=400) 
#%% Plot trends
z_chem=np.nanmean(data_comb.z_maxdens[data_comb.z_maxdens>200])
fig,ax=plt.subplots(2,3,figsize=(10,10),sharey=True)
colval=[(0,0,0),(0, 0, 0.8),(0.8,0,0)]
hp_all=[]
for kprof in np.arange(len(data_comb_periods["time0_periods"])):
    
    hp,=ax[0,0].plot(data_comb_periods.meanprof_Temp_avg[:,kprof],data_comb_periods.depth_interp,
            color=colval[kprof])
    hp_all.append(hp)
    ax[0,0].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_Temp_avg[:,kprof]-data_comb_periods.meanprof_Temp_std[:,kprof], 
                           data_comb_periods.meanprof_Temp_avg[:,kprof]+data_comb_periods.meanprof_Temp_std[:,kprof],
                           color=colval[kprof],alpha=0.2)
    
    
    ax[0,1].plot(data_comb_periods.meanprof_Cond_avg[:,kprof],data_comb_periods.depth_interp,
            color=colval[kprof])
    ax[0,1].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_Cond_avg[:,kprof]-data_comb_periods.meanprof_Cond_std[:,kprof], 
                           data_comb_periods.meanprof_Cond_avg[:,kprof]+data_comb_periods.meanprof_Cond_std[:,kprof],
                           color=colval[kprof],alpha=0.2)
    
    ax[0,2].plot(data_comb_periods.meanprof_rho_avg[:,kprof],data_comb_periods.depth_interp,
            color=colval[kprof])
    ax[0,2].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_rho_avg[:,kprof]-data_comb_periods.meanprof_rho_std[:,kprof], 
                           data_comb_periods.meanprof_rho_avg[:,kprof]+data_comb_periods.meanprof_rho_std[:,kprof],
                           color=colval[kprof],alpha=0.2)

    if kprof>0:
        dt=np.mean([data_comb_periods.time0_periods[kprof],data_comb_periods.timef_periods[kprof]])-np.mean([data_comb_periods.time0_periods[kprof-1],data_comb_periods.timef_periods[kprof-1]])
        ax[1,0].plot((data_comb_periods.meanprof_Temp_avg[:,kprof]-data_comb_periods.meanprof_Temp_avg[:,kprof-1])/(dt/(3600*24*365)),data_comb_periods.depth_interp,
            color=colval[kprof])
        ax[1,1].plot((data_comb_periods.meanprof_Cond_avg[:,kprof]-data_comb_periods.meanprof_Cond_avg[:,kprof-1])/(dt/(3600*24*365)),data_comb_periods.depth_interp,
            color=colval[kprof])
        ax[1,2].plot((data_comb_periods.meanprof_rho_avg[:,kprof]-data_comb_periods.meanprof_rho_avg[:,kprof-1])/(dt/(3600*24*365)),data_comb_periods.depth_interp,
            color=colval[kprof])
    else:
        ax[1,0].plot(data_comb_periods.meantrendprof_Temp_avg[:,kprof],data_comb_periods.depth_interp,
                  color=colval[kprof])
        ax[1,1].plot(data_comb_periods.meantrendprof_Cond_avg[:,kprof],data_comb_periods.depth_interp,
                color=colval[kprof])
        ax[1,2].plot(data_comb_periods.meantrendprof_rho_avg[:,kprof],data_comb_periods.depth_interp,
                color=colval[kprof])
    
    # ax[1,0].plot(data_comb_periods.meantrendprof_Temp_avg[:,kprof],data_comb_periods.depth_interp,
    #         color=colval[kprof])
    # # ax[1,0].fill_betweenx(data_comb_periods.depth_interp, 
    # #                         data_comb_periods.meantrendprof_Temp_avg[:,kprof]-data_comb_periods.meantrendprof_Temp_std[:,kprof], 
    # #                         data_comb_periods.meantrendprof_Temp_avg[:,kprof]+data_comb_periods.meantrendprof_Temp_std[:,kprof],
    # #                         color=colval[kprof],alpha=0.2)
    
    # ax[1,1].plot(data_comb_periods.meantrendprof_Cond_avg[:,kprof],data_comb_periods.depth_interp,
    #         color=colval[kprof])
    # # ax[1,1].fill_betweenx(data_comb_periods.depth_interp, 
    # #                         data_comb_periods.meantrendprof_Cond_avg[:,kprof]-data_comb_periods.meantrendprof_Cond_std[:,kprof], 
    # #                         data_comb_periods.meantrendprof_Cond_avg[:,kprof]+data_comb_periods.meantrendprof_Cond_std[:,kprof],
    # #                         color=colval[kprof],alpha=0.2)
    
    # ax[1,2].plot(data_comb_periods.meantrendprof_rho_avg[:,kprof],data_comb_periods.depth_interp,
    #         color=colval[kprof])
    # # ax[1,2].fill_betweenx(data_comb_periods.depth_interp, 
    # #                         data_comb_periods.meantrendprof_rho_avg[:,kprof]-data_comb_periods.meantrendprof_rho_std[:,kprof], 
    # #                         data_comb_periods.meantrendprof_rho_avg[:,kprof]+data_comb_periods.meantrendprof_rho_std[:,kprof],
    # #                         color=colval[kprof],alpha=0.2)

for k in [0,1,2]:
    xlimval=ax[0,k].get_xlim()
    ax[0,k].plot(xlimval,[z_chem,z_chem],'--k')
    ax[0,k].set_xlim(xlimval)
    xlimval=ax[1,k].get_xlim()
    ax[1,k].plot(xlimval,[z_chem,z_chem],'--k')
    ax[1,k].set_xlim(xlimval)


ax[0,0].set_ylim(220,280)
ax[0,0].invert_yaxis()
ax[0,0].set_ylabel('Depth [m]')
ax[0,0].set_xlabel('Temp [°C]')
#ax[0,0].legend(handles=[hp_all[i] for i in  [0,1,2]],labels=['Reference','Before extraction','During extraction'],fontsize=8,loc='center right')
ax[0,1].set_xlabel('Cond [mS.cm$^{-1}$]')
ax[0,2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')
ax[1,0].set_xlabel('Temp trend [°C.yr$^{-1}$]')
ax[1,1].set_xlabel('Cond trend [mS.cm$^{-1}$.yr$^{-1}$]')
ax[1,2].set_xlabel('$\\rho$ [kg.m$^{-3}$.yr$^{-1}$]')

fig.savefig("Figures/trends_zoom.png",dpi=400) 

#%% Close datasets
data_comb.close()
data_comb_periods.close()
