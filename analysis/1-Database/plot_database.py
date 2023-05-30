# -*- coding: utf-8 -*-
"""
Create figures from database.

@author: T. Doda
"""
import netCDF4
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['svg.fonttype'] = 'none' # To export text as text
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
savefig_bool=False
# nc_gov = netCDF4.Dataset(database_files[0], mode='r', format='NETCDF4_CLASSIC')
# nc_KW = netCDF4.Dataset(database_files[1], mode='r', format='NETCDF4_CLASSIC')
# nc_comb=netCDF4.Dataset(database_files[2], mode='r', format='NETCDF4_CLASSIC')
# nc_gov.close()
# nc_KW.close()
# nc_comb.close()

data_gov=xr.open_dataset(database_files[0])
data_KW=xr.open_dataset(database_files[1])
data_comb=xr.open_dataset(database_files[2])
data_comb_periods=xr.open_dataset(database_files[3],decode_times=False)
data_comb_all=xr.open_dataset(database_files[4])
print('Data loaded!')
breakpoint()
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

if savefig_bool:
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

if savefig_bool:
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

if savefig_bool:
    fig.savefig("Figures/all_deep_profiles.png",dpi=400) 
    
#%% Plot averaged profiles
z_chem=np.nanmean(data_comb.z_maxdens[data_comb.z_maxdens>200])
datetime_periods=[[datetime.utcfromtimestamp(data_comb_periods.time0_periods.values[i]) for i in [0,1,2]],
                  [datetime.utcfromtimestamp(data_comb_periods.timef_periods.values[i]) for i in [0,1,2]]]
z_chem_periods=[np.nanmean(data_comb.z_maxdens[np.logical_and(data_comb.z_maxdens>200,data_comb.time.values>np.datetime64(datetime_periods[0][i]),data_comb.time.values<np.datetime64(datetime_periods[1][i]))]) for i in [0,1,2]]
fig,ax=plt.subplots(2,3,figsize=(10,10),sharey=True)
colval=[(0,0,0),(0, 0, 0.8),(0.8,0,0)]
xlimval_all=[[(23.5,25.5),(2.5,5.5),(999,1001)],[(-0.05,0.05),(-0.06,0.06),(-0.03,0.03)]]
hp_all=[]
fig_zoom=True
for kprof in np.arange(len(data_comb_periods["time0_periods"])):
    
    hp,=ax[0,0].plot(data_comb_periods.meanprof_Temp_avg[:,kprof],data_comb_periods.depth_interp,
            color=colval[kprof])
    hp_all.append(hp)
    ax[0,0].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_Temp_avg[:,kprof]-data_comb_periods.meanprof_Temp_std[:,kprof], 
                           data_comb_periods.meanprof_Temp_avg[:,kprof]+data_comb_periods.meanprof_Temp_std[:,kprof],
                           color=colval[kprof],alpha=0.2)
    # ax[0,0].plot(xlimval_all[0][0],[z_chem_periods[kprof],z_chem_periods[kprof]],'--',color=colval[kprof])
    
    
    ax[0,1].plot(data_comb_periods.meanprof_Cond_avg[:,kprof],data_comb_periods.depth_interp,
            color=colval[kprof])
    ax[0,1].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_Cond_avg[:,kprof]-data_comb_periods.meanprof_Cond_std[:,kprof], 
                           data_comb_periods.meanprof_Cond_avg[:,kprof]+data_comb_periods.meanprof_Cond_std[:,kprof],
                           color=colval[kprof],alpha=0.2)
    # ax[0,1].plot(xlimval_all[0][1],[z_chem_periods[kprof],z_chem_periods[kprof]],'--',color=colval[kprof])
    
    ax[0,2].plot(data_comb_periods.meanprof_rho_avg[:,kprof],data_comb_periods.depth_interp,
            color=colval[kprof])
    ax[0,2].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_rho_avg[:,kprof]-data_comb_periods.meanprof_rho_std[:,kprof], 
                           data_comb_periods.meanprof_rho_avg[:,kprof]+data_comb_periods.meanprof_rho_std[:,kprof],
                           color=colval[kprof],alpha=0.2)
    # ax[0,2].plot(xlimval_all[0][2],[z_chem_periods[kprof],z_chem_periods[kprof]],'--',color=colval[kprof])

    if kprof>0:
        dt=np.mean([data_comb_periods.time0_periods[kprof],data_comb_periods.timef_periods[kprof]])-np.mean([data_comb_periods.time0_periods[kprof-1],data_comb_periods.timef_periods[kprof-1]])
        ax[1,0].plot((data_comb_periods.meanprof_Temp_avg[:,kprof]-data_comb_periods.meanprof_Temp_avg[:,kprof-1])/(dt/(3600*24*365)),data_comb_periods.depth_interp,
            color=colval[kprof])
        # ax[1,0].plot(xlimval_all[1][0],[z_chem_periods[kprof],z_chem_periods[kprof]],'--',color=colval[kprof])
        ax[1,1].plot((data_comb_periods.meanprof_Cond_avg[:,kprof]-data_comb_periods.meanprof_Cond_avg[:,kprof-1])/(dt/(3600*24*365)),data_comb_periods.depth_interp,
            color=colval[kprof])
        # ax[1,1].plot(xlimval_all[1][1],[z_chem_periods[kprof],z_chem_periods[kprof]],'--',color=colval[kprof])
        ax[1,2].plot((data_comb_periods.meanprof_rho_avg[:,kprof]-data_comb_periods.meanprof_rho_avg[:,kprof-1])/(dt/(3600*24*365)),data_comb_periods.depth_interp,
            color=colval[kprof])
        # ax[1,2].plot(xlimval_all[1][2],[z_chem_periods[kprof],z_chem_periods[kprof]],'--',color=colval[kprof])
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
    xlimval=xlimval_all[0][k]
    ax[0,k].plot(xlimval,[z_chem,z_chem],'--k')
    ax[0,k].set_xlim(xlimval)
    xlimval=xlimval_all[1][k]
    ax[1,k].plot(xlimval,[z_chem,z_chem],'--k')
    ax[1,k].set_xlim(xlimval)

time_periods=np.array([data_comb_periods.time0_periods.values,data_comb_periods.timef_periods.values-1])
yearstr_periods=[[str(datetime.utcfromtimestamp(time_periods[0,i]).year) for i in [0,1,2]],
               [str(datetime.utcfromtimestamp(time_periods[1,i]).year) for i in [0,1,2]]]
if fig_zoom:
    ax[0,0].set_ylim(220,280)
    figname="avgprof_zoom"
    legloc='upper center'
else:
    figname="avgprof"
    legloc='center right'
ax[0,0].legend(handles=[hp_all[i] for i in  [0,1,2]],labels=['Reference ({}-{})'.format(yearstr_periods[0][0],yearstr_periods[1][0]),
                                                             'Before extraction ({}-{})'.format(yearstr_periods[0][1],yearstr_periods[1][1]),
                                                             'During extraction ({}-{})'.format(yearstr_periods[0][2],yearstr_periods[1][2])],fontsize=8,loc=legloc)
ax[0,0].invert_yaxis()
ax[0,0].set_ylabel('Depth [m]')
ax[0,0].set_xlabel('Temperature [°C]')
ax[0,1].set_xlabel('Conductivity [mS.cm$^{-1}$]')
ax[0,2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')
ax[1,0].set_xlabel('Temperature trend [°C.yr$^{-1}$]')
ax[1,0].set_ylabel('Depth [m]')
ax[1,1].set_xlabel('Conductivity trend [mS.cm$^{-1}$.yr$^{-1}$]')
ax[1,2].set_xlabel('Density trend [kg.m$^{-3}$.yr$^{-1}$]')

if savefig_bool:
    #fig.savefig("Figures/"+figname+".png",dpi=400) 
    
    fig.savefig("Figures/"+figname+".svg")  
    print('Figure saved')
#%% Plot trends
zchem_series=data_comb.z_maxdens[data_comb.z_maxdens>200]
datechem_series=data_comb.time[data_comb.z_maxdens>200]
date_extract=np.datetime64(datetime(2016,1,1))
xlimval=(datetime(2008,1,1),datetime(2023,1,1))
ylimval=(254,266)


pfit_gov,t_gov,zfit_gov,R2_gov=regression_period(data_gov.time.values.astype(np.int64)*1e-9,data_gov.z_maxdens,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
pfit_KW,t_KW,zfit_KW,R2_KW=regression_period(data_KW.time.values.astype(np.int64)*1e-9,data_KW.z_maxdens,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
pfit_comb,t_comb,zfit_comb,R2_comb=regression_period(data_comb.time.values.astype(np.int64)*1e-9,data_comb.z_maxdens,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())

fig,ax=plt.subplots(3,1,figsize=(10,8),sharey=True,sharex=True)
ax[0].plot(data_gov.time[data_gov.z_maxdens>200],data_gov.z_maxdens[data_gov.z_maxdens>200],'.-',color='C0')
ax[0].plot([date_extract,date_extract],ylimval,'-b')
ax[0].plot([datetime.utcfromtimestamp(int(t_gov[0][i])) for i in np.arange(len(t_gov[0]))],zfit_gov[0],'--r')
ax[0].plot([datetime.utcfromtimestamp(int(t_gov[1][i])) for i in np.arange(len(t_gov[1]))],zfit_gov[1],'--r')
ax[0].set_ylabel('$z_{\\rm chem}$ [m]')
xtext=date_extract+0.25*(np.datetime64(xlimval[1])-np.datetime64(xlimval[0]))
ytext=ylimval[0]+0.95*(ylimval[1]-ylimval[0])
# ax[0].text(xtext,ytext,"z[m] = {:.1f} t[yr]+{:.1f}\n $R^2$ = {:.2f}".format(pfit_gov[1][0]*3600*24*365,pfit_gov[1][1],R2_gov[1]),
#            color='r',horizontalalignment='center',verticalalignment='center',bbox={"facecolor":"grey","alpha":0.5})
ax[0].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_gov[1][0]*3600*24*365,R2_gov[1]),
           color='r',horizontalalignment='center',verticalalignment='top',bbox={"facecolor":"grey","alpha":0.5})
ax[0].set_ylim(ylimval)
ax[0].set_xlim(xlimval)
ax[0].set_title('Government')

ax[1].plot(data_KW.time[data_KW.z_maxdens>200],data_KW.z_maxdens[data_KW.z_maxdens>200],'.-',color='C1')
ax[1].plot([date_extract,date_extract],ylimval,'-b')
ax[1].plot([datetime.utcfromtimestamp(int(t_KW[0][i])) for i in np.arange(len(t_KW[0]))],zfit_KW[0],'--r')
ax[1].plot([datetime.utcfromtimestamp(int(t_KW[1][i])) for i in np.arange(len(t_KW[1]))],zfit_KW[1],'--r')
ax[1].set_ylabel('$z_{\\rm chem}$ [m]')
ax[1].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_KW[1][0]*3600*24*365,R2_KW[1]),
           color='r',horizontalalignment='center',verticalalignment='top',bbox={"facecolor":"grey","alpha":0.5})
ax[1].set_title('Kivuwatt')


ax[2].plot(data_comb.time[data_comb.z_maxdens>200],data_comb.z_maxdens[data_comb.z_maxdens>200],'k-')
ax[2].plot(data_gov.time[data_gov.z_maxdens>200],data_gov.z_maxdens[data_gov.z_maxdens>200],'.',color='C0')
ax[2].plot(data_KW.time[data_KW.z_maxdens>200],data_KW.z_maxdens[data_KW.z_maxdens>200],'.',color='C1')
ax[2].plot([date_extract,date_extract],ylimval,'-b')
ax[2].plot([datetime.utcfromtimestamp(int(t_comb[0][i])) for i in np.arange(len(t_comb[0]))],zfit_comb[0],'--r')
ax[2].plot([datetime.utcfromtimestamp(int(t_comb[1][i])) for i in np.arange(len(t_comb[1]))],zfit_comb[1],'--r')
ax[2].set_ylabel('$z_{\\rm chem}$ [m]')
ax[2].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_comb[1][0]*3600*24*365,R2_comb[1]),
           color='r',horizontalalignment='center',verticalalignment='top',bbox={"facecolor":"grey","alpha":0.5})
ax[2].set_title('Combined')

if savefig_bool:
    #fig.savefig("Figures/trend_zchem.png",dpi=400) 
    
    fig.savefig("Figures/trend_zchem.svg")  
    print('Figure saved')


#%% Close datasets
data_gov.close()
data_KW.close()
data_comb.close()
data_comb_periods.close()
data_comb_all.close()