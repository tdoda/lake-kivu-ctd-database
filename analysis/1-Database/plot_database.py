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
import matplotlib.dates as mdates
plt.rcParams['svg.fonttype'] = 'none' # To export text as text
import pandas as pd
from datetime import datetime, timezone
import math
import cmocean
import xarray as xr
from scipy.stats.distributions import  t
from geopy import distance
import geopandas as gpd
from shapely.geometry import Point, Polygon
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *
from functions_plot import *


plt.close ('all')
#%% Data files

#database_files=["database_gov_250m.nc","database_Kivuwatt_250m.nc","database_combined_250m.nc","database_combined_250m_periods.nc","database_combined_0m.nc"]
database_files=["database_gov2_260m.nc","database_Kivuwatt2_260m.nc","database_combined2_260m.nc","database_combined2_260m_periods.nc","database_combined2_0m.nc"]
#file_flows="../../../../Kivu_monitoring/Kivuwatt/Hourly flows 2016-2022.xlsx"
file_flows="F:/Backup_Tomy/Data/Kivu_monitoring/Kivuwatt/Hourly flows 2016-2022.xlsx"


savefig_bool=False

data_gov=xr.open_dataset(database_files[0])
data_KW=xr.open_dataset(database_files[1])
data_comb=xr.open_dataset(database_files[2])
data_comb_periods=xr.open_dataset(database_files[3],decode_times=False)
data_comb_all=xr.open_dataset(database_files[4])
data_flows=pd.read_excel(file_flows,names=["Date","Intake","Reject","Wash","Gas","Consumption","Sweet_flare","Sweet_pilot","Raw_flare","Sweet_net"])
tonsh_to_m3s=3600 # Conversion factor assuming rho=1000 kg/m^3=1 ton/m^3

date_prof_all=[datetime.utcfromtimestamp(data_comb_all.time.values[i].astype(np.int64) * 1e-9) for i in range(len(data_comb_all.time))]
date_prof_deep=[datetime.utcfromtimestamp(data_comb.time.values[i].astype(np.int64) * 1e-9) for i in range(len(data_comb.time))]
# Bathymetry
bathy_data=pd.read_csv('../0-Bathymetry/bathymetry_grid_1mdeg_1dobs.csv', sep=",",index_col=0) 
bathy_depth=bathy_data.values
bathy_long=bathy_data.columns.values.astype('float')
bathy_lat=bathy_data.index.values
# Hypsometry
dlat=bathy_lat[1]-bathy_lat[0] #[°]
dx_bathy=distance.distance((np.mean(bathy_lat),np.mean(bathy_long)), (np.mean(bathy_lat)+dlat,np.mean(bathy_long))).m
dy_bathy=distance.distance((np.mean(bathy_lat),np.mean(bathy_long)), (np.mean(bathy_lat),np.mean(bathy_long)+dlat)).m
hypso_z,hypso_A=compute_hypso(-bathy_depth,dA=dx_bathy*dy_bathy,dz=1) #m, m^2
df_hypso=pd.read_csv('../0-Bathymetry/hypsometry_1m.csv',sep=',',names=['z','A'],skiprows=1) 

lakecontour=gpd.read_file('..\..\..\..\Bathymetry\Kivu_Lake.shp')
polycontour=Polygon(list(lakecontour["geometry"][0].exterior.coords)) # Outside contour
xcont,ycont=polycontour.exterior.xy
xpoly=[xcont]
ypoly=[ycont]
polyinner=[] # Islands
for intpoly in lakecontour["geometry"][0].interiors:
    polyinner.append(Polygon(list(intpoly.coords)))
    xcont,ycont=polyinner[-1].exterior.xy
    xpoly.append(xcont)
    ypoly.append(ycont)

# Coordinates of GEP    
coord_KW=[29.202352,-2.087932]
coord_KP1=[29.242921,-1.732214]

print('Data loaded!')
breakpoint()

#%% Categorize profile depending on location
dist_treshold=2 # km
dist_prof_to_KW=np.array([np.nan]*len(data_comb_all.time))
dist_prof_to_KP=np.array([np.nan]*len(data_comb_all.time))
for kprof in range(len(data_comb_all.time)):
    if ~np.isnan(data_comb_all.longitude.values[kprof]):
        dist_prof_to_KW[kprof]=distance.distance((data_comb_all.longitude.values[kprof],data_comb_all.latitude.values[kprof]), tuple(coord_KW)).km
        dist_prof_to_KP[kprof]=distance.distance((data_comb_all.longitude.values[kprof],data_comb_all.latitude.values[kprof]), tuple(coord_KP1)).km
bool_closeKW=dist_prof_to_KW<dist_treshold
bool_closeKP=dist_prof_to_KP<dist_treshold
#%% Plot map
fig,ax=plt.subplots(figsize=(5,5))
#hmesh=ax.pcolormesh(bathy_long,bathy_lat,bathy_depth,cmap=cmocean.cm.ice)
hmesh=ax.pcolormesh(bathy_long,bathy_lat,bathy_depth,cmap='viridis',vmin=np.nanmin(bathy_depth),vmax=0)
cb=plt.colorbar(hmesh)

# Add boundaries:
for kpoly in range(len(xpoly)):
    ax.plot(xpoly[kpoly],ypoly[kpoly],'-k',linewidth=0.5)
    
# Add location profiles 
ax.plot(data_comb_all.longitude.values,data_comb_all.latitude.values,'k.') # All profiles
# ax.plot(data_gov.longitude.values,data_gov.latitude.values,'m.')
# ax.plot(data_KW.longitude.values,data_KW.latitude.values,'g.')
ax.plot(data_comb_all.longitude.values[bool_closeKW],data_comb_all.latitude.values[bool_closeKW],'r.')
ax.plot(data_comb_all.longitude.values[bool_closeKP],data_comb_all.latitude.values[bool_closeKP],'r.')

# Add location of GEP
ax.plot(coord_KW[0],coord_KW[1],'rx')
ax.plot(coord_KP1[0],coord_KP1[1],'rx')

ax.axis('equal')
ax.set_xlabel('Longitude [°]')
ax.set_ylabel('Latitude [°]')
cb.set_label('Depth [m]')
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
zchem=data_comb.z_maxdens_smooth.copy()
zchem2=data_comb.z_chemfit.copy()
#zchem[data_comb.z_maxdens<200]=np.nan
ax[2].plot(data_comb.time,zchem,'-r')
ax[2].plot(data_comb.time,zchem2,'-k')
ax[2].invert_yaxis()
cb3=fig.colorbar(c3, ax=ax[2])
cb3.set_label('$\\rho$ [kg.m$^{-3}$]')
ax[2].set_ylabel('Depth [m]')
ax[2].tick_params(axis='x',labelrotation=45)

if savefig_bool:
    fig.savefig("Figures/timeseries_grid.png",dpi=400)

#%% Plot all profiles
boolper=np.logical_and(data_comb_all.time>np.datetime64(datetime(2022,1,1)),data_comb_all.time<np.datetime64(datetime(2022,3,1)))
indprof_all=np.where(np.logical_and(np.logical_and(np.logical_and(data_comb_all.max_depth>300,data_comb_all.min_depth<10),bool_closeKW),boolper))[0]

fig,ax=plt.subplots(1,3,figsize=(10,5),sharey=True)
colval=plt.get_cmap('viridis',len(indprof_all))
colval2=[(0, 0, 0.8),(0,0.8,0)]
hplots_all=[None]*len(indprof_all)

for kprof in range(len(indprof_all)):
    print('Progress: {:.1f} %'.format(kprof/len(indprof_all)*100))
    
    hplots_all[kprof],=ax[0].plot(data_comb_all.Temp[:,indprof_all[kprof]],data_comb_all.depth_interp,
            color=colval(kprof))
    
    ax[1].plot(data_comb_all.SALIN[:,indprof_all[kprof]],data_comb_all.depth_interp,
            color=colval(kprof))
    
    ax[2].plot(data_comb_all.rho[:,indprof_all[kprof]],data_comb_all.depth_interp,
            color=colval(kprof))
    # ax[2].plot(data_comb_all.rho[:,kprof],data_comb_all.depth_interp,
    #          color=colval2[int(data_comb_all.data_type[kprof])])

ax[0].invert_yaxis()
ax[0].set_ylabel('Depth [m]')
ax[0].set_xlabel('Temp [°C]')
indselect=np.arange(0,len(indprof_all),1)
ax[1].legend(handles=[hplots_all[i] for i in  indselect],labels=[date_prof_all[indprof_all[i]] for i in  indselect],fontsize=8,loc='upper right')
ax[1].set_xlabel('S [g.kg$^{-1}$]')
ax[2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')

if savefig_bool:
    fig.savefig("Figures/all_profiles.png",dpi=400) 
#%% Plot deep profiles

fig,ax=plt.subplots(1,3,figsize=(10,5),sharey=True)
colval=plt.get_cmap('viridis',len(data_comb["time"]))
colval2=[(0, 0, 0.8),(0,0.8,0)]
hplots_deep=[None]*len(data_comb["time"])
for kprof in np.arange(len(data_comb["time"])):
    print('Progress: {:.1f} %'.format(kprof/len(data_comb["time"])*100))
    
    hplots_deep[kprof],=ax[0].plot(data_comb.Temp[:,kprof],data_comb.depth_interp,
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
yearselect=np.arange(2008,2023,1)
yearall=[date_prof_deep[i].year for i in range(len(date_prof_deep))]
#indselect=np.arange(0,len(data_comb["time"]),50)
indselect=[np.where(yearall>=yearval)[0][0] for yearval in yearselect]
ax[1].legend(handles=[hplots_deep[i] for i in  indselect],labels=[date_prof_deep[i].year for i in  indselect],fontsize=8,loc='upper right')
ax[1].set_xlabel('Cond [mS.cm$^{-1}$]')
ax[2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')

if savefig_bool:
    fig.savefig("Figures/all_deep_profiles.png",dpi=400) 
    

#%% Plot shifted density profiles and chemocline depth (LONG!)
fig,ax=plt.subplots(1,1,figsize=(10,3))
drho=0.1
namevar=["maxdens_smooth","meta_middle","middens","chemfit"]
colvar=['.-r','.-g','.-m','.-b']
for kvar in range(len(namevar)):
    exec('rho_'+namevar[kvar]+'=[np.nan]*len(data_comb["time"])')

for kprof in np.arange(len(data_comb["time"])): 
    ax.plot(data_comb["rho"][:,kprof]+drho*kprof,data_comb["depth_interp"],'-k')
    for kvar in range(len(namevar)):
        if not np.isnan(data_comb["z_"+namevar[kvar]][kprof]):
            exec('rho_'+namevar[kvar]+"[kprof]=data_comb['rho'].values[np.where(data_comb['depth_interp']>=data_comb['z_"+namevar[kvar]+"'][kprof])[0][0],kprof]+drho*kprof")

for kvar in range(len(namevar)):
    exec("ax.plot(rho_"+namevar[kvar]+",data_comb['z_"+namevar[kvar]+"'],'"+colvar[kvar]+"')")
ax.invert_yaxis()
ax.set_ylabel('Depth [m]')
ax.set_xlabel('$\\rho$ [kg.m$^{-3}$] (each profile shifted by '+str(drho)+' kg.m$^{-3}$)')
fig.set_tight_layout(True)

#%% Averaged density profile fit
colval=[(0,0,0),(0, 0, 0.8),(0,0.8,0)]
xlimval=(999.5,1001)
fig,ax=plt.subplots(1,3,figsize=(10,8),sharex=True,sharey=True)
for kprof in np.arange(len(data_comb_periods["time0_periods"])):
    rhotop=np.nanmean(data_comb_periods.meanprof_rho_avg[np.logical_and(data_comb_periods.depth_interp>=data_comb.z_bounds[0],data_comb_periods.depth_interp<=data_comb.z_bounds[0]+5),kprof])
    rhobot=np.nanmean(data_comb_periods.meanprof_rho_avg[np.logical_and(data_comb_periods.depth_interp>=data_comb.z_bounds[1]-5,data_comb_periods.depth_interp<=data_comb.z_bounds[1]),kprof])
    zchemfit, deltafit,pcov,info_dict=fit_rho(data_comb_periods.depth_interp,data_comb_periods.meanprof_rho_avg[:,kprof],rhotop,rhobot,data_comb.z_bounds,[5,260])
    std_param=np.sqrt(np.diag(pcov))
    alpha=1-0.95
    tval=t.ppf(1-alpha/2,len(data_comb_periods.depth_interp)-2) # To get (1-alpha)% CI with degree of freedom=n-nb parameters (tval=1 for 67% CI)
    CI_param=np.array([[zchemfit-std_param[0]*tval,zchemfit+std_param[0]*tval],[deltafit-std_param[1]*tval, deltafit+std_param[1]*tval]])
    rhofit=densprofile(data_comb_periods.depth_interp,deltafit[0],zchemfit[0],rhotop,rhobot)
    grad_rho=np.abs(np.gradient(data_comb_periods.meanprof_rho_avg[np.logical_and(data_comb_periods.depth_interp>=data_comb.z_bounds[0],data_comb_periods.depth_interp<=data_comb.z_bounds[1]),kprof], axis=0))
    depthval=data_comb_periods.depth_interp[np.logical_and(data_comb_periods.depth_interp>=data_comb.z_bounds[0],data_comb_periods.depth_interp<=data_comb.z_bounds[1])]
    zmaxgrad=depthval[np.nanargmax(grad_rho,axis=0)]
    
    ax[kprof].plot(data_comb_periods.meanprof_rho_avg[:,kprof],data_comb_periods.depth_interp,color=colval[kprof])
    ax[kprof].fill_betweenx(data_comb_periods.depth_interp, 
                           data_comb_periods.meanprof_rho_avg[:,kprof]-data_comb_periods.meanprof_rho_std[:,kprof], 
                           data_comb_periods.meanprof_rho_avg[:,kprof]+data_comb_periods.meanprof_rho_std[:,kprof],
                           color=colval[kprof],alpha=0.2)
    ax[kprof].plot(xlimval,[zmaxgrad]*2,':',color=colval[kprof])
    ax[kprof].plot(rhofit,data_comb_periods.depth_interp,'-r')
    ax[kprof].plot(xlimval,[zchemfit-deltafit/2]*2,'--r')
    ax[kprof].plot(xlimval,[zchemfit+deltafit/2]*2,'--r')
    ax[kprof].plot(xlimval,[zchemfit]*2,':r')
    ax[kprof].text(xlimval[0]+0.98*np.diff(xlimval),data_comb.z_bounds.values[0]+0.01*np.diff(data_comb.z_bounds.values),"$z_{{\\rm chem}} = {:.1f}\\pm{:.1f}$ m\n $\\delta_{{\\rm meta}} = {:.1f}\\pm{:.1f}$ m".format(zchemfit[0],std_param[0],deltafit[0],std_param[1]),
               color='r',horizontalalignment='right',verticalalignment='top',bbox={"facecolor":"grey","alpha":0.1})
ax[0].set_ylim(data_comb.z_bounds)
ax[0].set_xlim(xlimval)
ax[0].invert_yaxis()
#%% Plot averaged profiles
z_chem=np.nanmean(data_comb.z_maxdens[data_comb.z_maxdens>200])
datetime_periods=[[datetime.utcfromtimestamp(data_comb_periods.time0_periods.values[i]) for i in [0,1,2]],
                  [datetime.utcfromtimestamp(data_comb_periods.timef_periods.values[i]) for i in [0,1,2]]]
z_chem_periods=[np.nanmean(data_comb.z_maxdens[np.logical_and(data_comb.z_maxdens>200,data_comb.time.values>np.datetime64(datetime_periods[0][i]),data_comb.time.values<np.datetime64(datetime_periods[1][i]))]) for i in [0,1,2]]
fig,ax=plt.subplots(2,3,figsize=(10,10),sharey=True)
colval=[(0,0,0),(0, 0, 0.8),(0,0.8,0)]
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

# All deep profiles
plot_trend_series(['z_maxdens_smooth','z_meta_middle','z_middens','z_chemfit'],data_comb,indprof=np.arange(len(data_comb.time)),intersect_lines=True)
#plot_trend_series(['z_maxdens_smooth','z_meta_middle','z_middens','z_chemfit'],data_comb_all,indprof=np.where(data_comb_all.max_depth>260)[0])

# Profiles near Kivuwatt
plot_trend_series(['z_maxdens_smooth','z_meta_middle','z_middens','z_chemfit'],data_comb_all,indprof=np.where(np.logical_and(data_comb_all.max_depth>260,bool_closeKW))[0],intersect_lines=True)
plot_trend_series(['delta_metafit'],data_comb_all,indprof=np.where(np.logical_and(data_comb_all.max_depth>260,bool_closeKW))[0],delta=True,intersect_lines=True,ylimval=(4,11))

# Profiles near KP1
plot_trend_series(['z_maxdens_smooth','z_meta_middle','z_middens','z_chemfit'],data_comb_all,indprof=np.where(np.logical_and(data_comb_all.max_depth>260,bool_closeKP))[0],intersect_lines=True)
plot_trend_series(['delta_metafit'],data_comb_all,indprof=np.where(np.logical_and(data_comb_all.max_depth>260,bool_closeKP))[0],delta=True,intersect_lines=True,ylimval=(4,11))

# for kmethod in range(len(methods_all)):
#     exec('zchem_gov=data_gov.'+methods_all[kmethod])
#     exec('zchem_KW=data_KW.'+methods_all[kmethod])
#     exec('zchem_comb=data_comb.'+methods_all[kmethod])
#     date_extract=np.datetime64(datetime(2016,1,1))
#     xlimval=(datetime(2008,1,1),datetime(2023,1,1))
#     ylimval=(254,266)
    
    
#     pfit_gov,t_gov,zfit_gov,R2_gov=regression_period(data_gov.time.values.astype(np.int64)*1e-9,zchem_gov,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
#     pfit_KW,t_KW,zfit_KW,R2_KW=regression_period(data_KW.time.values.astype(np.int64)*1e-9,zchem_KW,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
#     pfit_comb,t_comb,zfit_comb,R2_comb=regression_period(data_comb.time.values.astype(np.int64)*1e-9,zchem_comb,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
#     pfit_gov2,zfit_gov2,R2_gov2,pcov_gov2=regression_period_intersect(data_gov.time.values.astype(np.int64)*1e-9,zchem_gov,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
#     pfit_KW2,zfit_KW2,R2_KW2,pcov_KW2=regression_period_intersect(data_KW.time.values.astype(np.int64)*1e-9,zchem_KW,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
#     pfit_comb2,zfit_comb2,R2_comb2,pcov_comb2=regression_period_intersect(data_comb.time.values.astype(np.int64)*1e-9,zchem_comb,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
    
#     fig,ax=plt.subplots(3,1,figsize=(5,5),sharey=True,sharex=True)
#     fig.suptitle('Method: '+methods_all[kmethod],fontsize=14)

#     ax[0].plot(data_gov.time,zchem_gov,'.-',color='C0')
#     ax[0].plot([date_extract,date_extract],ylimval,'-b')
#     xtext=date_extract+0.25*(np.datetime64(xlimval[1])-np.datetime64(xlimval[0]))
#     ytext=ylimval[0]+0.95*(ylimval[1]-ylimval[0])
#     if intersect_lines:
#         ax[0].plot(data_gov.time,zfit_gov2,'--r')
#         ax[0].text(xtext,ytext,"dz/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_gov2[1][0]*3600*24*365,np.sqrt(pcov_gov2[2,2])*3600*24*365,R2_gov2[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
#     else:       
#         ax[0].plot([datetime.utcfromtimestamp(int(t_gov[0][i])) for i in np.arange(len(t_gov[0]))],zfit_gov[0],'--r')
#         ax[0].plot([datetime.utcfromtimestamp(int(t_gov[1][i])) for i in np.arange(len(t_gov[1]))],zfit_gov[1],'--r')
#         ax[0].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_gov[1][0]*3600*24*365,R2_gov[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
    
#     ax[0].set_ylabel('$z_{\\rm chem}$ [m]')
#     ax[0].set_ylim(ylimval)
#     ax[0].invert_yaxis()
#     ax[0].set_xlim(xlimval)
#     ax[0].set_title('Government')
    
#     ax[1].plot(data_KW.time,zchem_KW,'.-',color='C1')
#     ax[1].plot([date_extract,date_extract],ylimval,'-b')    
#     if intersect_lines:
#         ax[1].plot(data_KW.time,zfit_KW2,'--r')
#         ax[1].text(xtext,ytext,"dz/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_KW2[1][0]*3600*24*365,np.sqrt(pcov_KW2[2,2])*3600*24*365,R2_KW2[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})   
#     else:    
#         ax[1].plot([datetime.utcfromtimestamp(int(t_KW[0][i])) for i in np.arange(len(t_KW[0]))],zfit_KW[0],'--r')
#         ax[1].plot([datetime.utcfromtimestamp(int(t_KW[1][i])) for i in np.arange(len(t_KW[1]))],zfit_KW[1],'--r')
#         ax[1].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_KW[1][0]*3600*24*365,R2_KW[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
#     ax[1].set_ylabel('$z_{\\rm chem}$ [m]')

#     ax[1].set_title('Kivuwatt')
    
    
#     ax[2].plot(data_comb.time,zchem_comb,'k-')
#     ax[2].plot(data_gov.time,zchem_gov,'.',color='C0')
#     ax[2].plot(data_KW.time,zchem_KW,'.',color='C1')
#     ax[2].plot([date_extract,date_extract],ylimval,'-b')
#     if intersect_lines:
#         ax[2].plot(data_comb.time,zfit_comb2,'--r')
#         ax[2].text(xtext,ytext,"dz/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_comb2[1][0]*3600*24*365,np.sqrt(pcov_comb2[2,2])*3600*24*365,R2_comb2[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})   
#     else: 
#         ax[2].plot([datetime.utcfromtimestamp(int(t_comb[0][i])) for i in np.arange(len(t_comb[0]))],zfit_comb[0],'--r')
#         ax[2].plot([datetime.utcfromtimestamp(int(t_comb[1][i])) for i in np.arange(len(t_comb[1]))],zfit_comb[1],'--r')
#         ax[2].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_comb[1][0]*3600*24*365,R2_comb[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
#     ax[2].set_ylabel('$z_{\\rm chem}$ [m]')
#     ax[2].set_title('Combined')
    
#     if savefig_bool:
#         fig.savefig("Figures/trend_zchem_"+methods_all[kmethod]+".png",dpi=400)  
#         #fig.savefig("Figures/trend_zchem_"+methods_all[kmethod]+".svg")  
#         print('Figure saved')
        
#%% Plot trend of metalimnion thickness
# methods_all=['delta_metafit']
# intersect_lines=True

# for kmethod in range(len(methods_all)):
#     exec('zchem_gov=data_gov.'+methods_all[kmethod])
#     exec('zchem_KW=data_KW.'+methods_all[kmethod])
#     exec('zchem_comb=data_comb.'+methods_all[kmethod])
#     date_extract=np.datetime64(datetime(2016,1,1))
#     xlimval=(datetime(2008,1,1),datetime(2023,1,1))
#     ylimval=(4,11)
    
    
#     pfit_gov,t_gov,zfit_gov,R2_gov=regression_period(data_gov.time.values.astype(np.int64)*1e-9,zchem_gov,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
#     pfit_KW,t_KW,zfit_KW,R2_KW=regression_period(data_KW.time.values.astype(np.int64)*1e-9,zchem_KW,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
#     pfit_comb,t_comb,zfit_comb,R2_comb=regression_period(data_comb.time.values.astype(np.int64)*1e-9,zchem_comb,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
#     pfit_gov2,zfit_gov2,R2_gov2,pcov_gov2=regression_period_intersect(data_gov.time.values.astype(np.int64)*1e-9,zchem_gov,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
#     pfit_KW2,zfit_KW2,R2_KW2,pcov_KW2=regression_period_intersect(data_KW.time.values.astype(np.int64)*1e-9,zchem_KW,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
#     pfit_comb2,zfit_comb2,R2_comb2,pcov_comb2=regression_period_intersect(data_comb.time.values.astype(np.int64)*1e-9,zchem_comb,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
    
#     fig,ax=plt.subplots(3,1,figsize=(5,5),sharey=True,sharex=True)
#     fig.suptitle('Method: '+methods_all[kmethod],fontsize=14)

#     ax[0].plot(data_gov.time,zchem_gov,'.-',color='C0')
#     ax[0].plot([date_extract,date_extract],ylimval,'-b')
#     xtext=date_extract+0.25*(np.datetime64(xlimval[1])-np.datetime64(xlimval[0]))
#     ytext=ylimval[0]+0.05*(ylimval[1]-ylimval[0])
#     if intersect_lines:
#         ax[0].plot(data_gov.time,zfit_gov2,'--r')
#         ax[0].text(xtext,ytext,"dz/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_gov2[1][0]*3600*24*365,np.sqrt(pcov_gov2[2,2])*3600*24*365,R2_gov2[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
#     else:       
#         ax[0].plot([datetime.utcfromtimestamp(int(t_gov[0][i])) for i in np.arange(len(t_gov[0]))],zfit_gov[0],'--r')
#         ax[0].plot([datetime.utcfromtimestamp(int(t_gov[1][i])) for i in np.arange(len(t_gov[1]))],zfit_gov[1],'--r')
#         ax[0].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_gov[1][0]*3600*24*365,R2_gov[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
    
#     ax[0].set_ylabel('$\\delta_{\\rm meta}$ [m]')
#     ax[0].set_ylim(ylimval)
#     ax[0].set_xlim(xlimval)
#     ax[0].set_title('Government')
    
#     ax[1].plot(data_KW.time,zchem_KW,'.-',color='C1')
#     ax[1].plot([date_extract,date_extract],ylimval,'-b')    
#     if intersect_lines:
#         ax[1].plot(data_KW.time,zfit_KW2,'--r')
#         ax[1].text(xtext,ytext,"dz/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_KW2[1][0]*3600*24*365,np.sqrt(pcov_KW2[2,2])*3600*24*365,R2_KW2[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})   
#     else:    
#         ax[1].plot([datetime.utcfromtimestamp(int(t_KW[0][i])) for i in np.arange(len(t_KW[0]))],zfit_KW[0],'--r')
#         ax[1].plot([datetime.utcfromtimestamp(int(t_KW[1][i])) for i in np.arange(len(t_KW[1]))],zfit_KW[1],'--r')
#         ax[1].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_KW[1][0]*3600*24*365,R2_KW[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
#     ax[1].set_ylabel('$\\delta_{\\rm meta}$ [m]')

#     ax[1].set_title('Kivuwatt')
    
    
#     ax[2].plot(data_comb.time,zchem_comb,'k-')
#     ax[2].plot(data_gov.time,zchem_gov,'.',color='C0')
#     ax[2].plot(data_KW.time,zchem_KW,'.',color='C1')
#     ax[2].plot([date_extract,date_extract],ylimval,'-b')
#     if intersect_lines:
#         ax[2].plot(data_comb.time,zfit_comb2,'--r')
#         ax[2].text(xtext,ytext,"dz/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_comb2[1][0]*3600*24*365,np.sqrt(pcov_comb2[2,2])*3600*24*365,R2_comb2[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})   
#     else: 
#         ax[2].plot([datetime.utcfromtimestamp(int(t_comb[0][i])) for i in np.arange(len(t_comb[0]))],zfit_comb[0],'--r')
#         ax[2].plot([datetime.utcfromtimestamp(int(t_comb[1][i])) for i in np.arange(len(t_comb[1]))],zfit_comb[1],'--r')
#         ax[2].text(xtext,ytext,"dz/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(pfit_comb[1][0]*3600*24*365,R2_comb[1]),
#                    color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
#     ax[2].set_ylabel('$\\delta_{\\rm meta}$ [m]')
#     ax[2].set_title('Combined')
    
    # if savefig_bool:
    #     fig.savefig("Figures/trend_deltachem_"+methods_all[kmethod]+".png",dpi=400)  
    #     #fig.savefig("Figures/trend_zchem_"+methods_all[kmethod]+".svg")  
    #     print('Figure saved')
    
#%% Heat, salt and mass balances (KW profiles)
indprof=np.where(np.logical_and(np.logical_and(data_comb_all.max_depth>300,data_comb_all.min_depth<10),bool_closeKW))[0]
#indprof=np.where(np.logical_and(np.logical_and(data_comb_all.max_depth>300,data_comb_all.min_depth<10),bool_closeKP))[0]
H,S,M=compute_balance(data_comb_all,indprof,hypso_z,hypso_A) # J, kg, kg
timeval=data_comb_all.time.values[indprof].astype('datetime64[s]') # Rounded seconds
datetime_extract=datetime(2016,1,1)

# Total:
boolsum=np.logical_and(hypso_z>=np.nanmax(data_comb_all.min_depth[indprof]),hypso_z<=np.nanmin(data_comb_all.max_depth[indprof]))
Htot=np.nansum(H[boolsum,:],axis=0)
Stot=np.nansum(S[boolsum,:],axis=0)
Mtot=np.nansum(M[boolsum,:],axis=0)

# In specific layers:
zlayer_top=[235,255]
zlayer_bot=[255,275]
Hlayer=np.full((len(zlayer_top),len(indprof)),np.nan)
Slayer=np.full((len(zlayer_top),len(indprof)),np.nan)
for kl in range(len(zlayer_top)):
    bool_depth=np.logical_and(hypso_z>=zlayer_top[kl],hypso_z<zlayer_bot[kl])
    Hlayer[kl,:]=np.nansum(H[bool_depth,:],axis=0)
    Slayer[kl,:]=np.nansum(S[bool_depth,:],axis=0)
    
    
# Above chemocline
zlayer_bot_chem=data_comb_all.z_maxdens_smooth.values[indprof]
Hlayer_chem=np.full((1,len(indprof)),np.nan)
Slayer_chem=np.full((1,len(indprof)),np.nan)
dz_S=20 # [m]
for kprof in range(len(indprof)):
    bool_depth=np.logical_and(hypso_z>=zlayer_bot_chem[kprof]-dz_S,hypso_z<zlayer_bot_chem[kprof]) 
    Hlayer_chem[0,kprof]=np.nansum(H[bool_depth,kprof],axis=0)
    Slayer_chem[0,kprof]=np.nansum(S[bool_depth,kprof],axis=0)
#%% Plot mass balance profiles (similar to conductivity, temperature, density profiles)
fig,ax=plt.subplots(1,3,figsize=(10,5),sharey=True)
colval=plt.get_cmap('viridis',len(indprof))
hplots_all=[None]*len(indprof)

for kprof in range(len(indprof)):
    print('Progress: {:.1f} %'.format(kprof/len(indprof)*100))
    
    hplots_all[kprof],=ax[0].plot(H[:,kprof]/1000,hypso_z,
            color=colval(kprof))
    
    ax[1].plot(S[:,kprof]/1000,hypso_z,color=colval(kprof))
    
    ax[2].plot(M[:,kprof]/1000,hypso_z,color=colval(kprof))
         

ax[0].invert_yaxis()
ax[0].set_ylabel('Depth [m]')
ax[0].set_xlabel('Heat [kJ/m]')
# indselect=np.arange(0,len(indprof),1)
# ax[1].legend(handles=[hplots_all[i] for i in  indselect],labels=[date_prof_all[indprof[i]] for i in  indselect],fontsize=8,loc='upper right')
ax[1].set_xlabel('Salt [tons/m]')
ax[2].set_xlabel('Water mass [tons/m]')

if savefig_bool:
    fig.savefig("Figures/mass_balance_profiles.png",dpi=400) 
    
#%% Plot time series in specific layers 

fig,ax=plt.subplots(len(zlayer_top),2,figsize=(10,7),sharex=True)
for kl in range(len(zlayer_top)):
    bool_depth=np.logical_and(hypso_z>=zlayer_top[kl],hypso_z<zlayer_bot[kl])
    ax[kl,0].plot(timeval,Hlayer[kl,:]/1e15,'k-')
    ax[kl,0].plot(timeval[data_comb_all.data_type[indprof]==0],Hlayer[kl,data_comb_all.data_type[indprof]==0]/1e15,'.')
    ax[kl,0].plot(timeval[data_comb_all.data_type[indprof]==1],Hlayer[kl,data_comb_all.data_type[indprof]==1]/1e15,'.')
    
    pfit_H,Hfit,R2_H,pcov_H=regression_period_intersect(timeval.astype(np.int64),Hlayer[kl,:]/1e15,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
    ax[kl,0].plot(timeval,Hfit,'--r')
    xlimval=mdates.num2date(ax[kl,0].get_xlim())
    ylimval=ax[kl,0].get_ylim()
    xtext=datetime_extract+0.25*(xlimval[1]-xlimval[0])
    ytext=ylimval[0]+0.05*(ylimval[1]-ylimval[0])
    if R2_H[1]>0.1:
        ax[kl,0].text(xtext,ytext,"dH/dt = {:.2f}$\\pm${:.2f} $10^3$ GJ/yr\n $R^2$ = {:.2f}".format(pfit_H[1][0]*1000*3600*24*365,np.sqrt(pcov_H[2,2])*1000*3600*24*365,R2_H[1]),
                   color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
    ax[kl,0].set_ylim(ylimval)
    ax[kl,0].plot([datetime_extract,datetime_extract],ylimval,'-b')
    ax[kl,0].set_ylabel('Heat in layer [$10^6$ GJ]')
    ax[kl,0].set_title('Layer {}-{} m'.format(zlayer_top[kl],zlayer_bot[kl]))
    
    ax[kl,1].plot(timeval,Slayer[kl,:]/1e9,'k-')
    ax[kl,1].plot(timeval[data_comb_all.data_type[indprof]==0],Slayer[kl,data_comb_all.data_type[indprof]==0]/1e9,'.')
    ax[kl,1].plot(timeval[data_comb_all.data_type[indprof]==1],Slayer[kl,data_comb_all.data_type[indprof]==1]/1e9,'.')
    pfit_S,Sfit,R2_S,pcov_S=regression_period_intersect(timeval.astype(np.int64),Slayer[kl,:]/1e9,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
    ax[kl,1].plot(timeval,Sfit,'--r')
    xlimval=mdates.num2date(ax[kl,1].get_xlim())
    ylimval=ax[kl,1].get_ylim()
    xtext=datetime_extract+0.25*(xlimval[1]-xlimval[0])
    ytext=ylimval[0]+0.05*(ylimval[1]-ylimval[0])
    ax[kl,1].text(xtext,ytext,"dS/dt = {:.2f}$\\pm${:.2f} ktons/yr\n $R^2$ = {:.2f}".format(pfit_S[1][0]*1000*3600*24*365,np.sqrt(pcov_S[2,2])*1000*3600*24*365,R2_S[1]),
               color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
    ax[kl,1].set_ylim(ylimval)
    ax[kl,1].plot([datetime_extract,datetime_extract],ylimval,'-b')
    ax[kl,1].set_ylabel('Salt in layer [Mtons]')
    ax[kl,1].set_title('Layer {}-{} m'.format(zlayer_top[kl],zlayer_bot[kl]))
         

if savefig_bool:
    fig.savefig("Figures/mass_balance_series.png",dpi=400) 

#%% Plot time series net values
fig,ax=plt.subplots(3,1,figsize=(10,5),sharex=True)
ax[0].plot(timeval[data_comb_all.data_type[indprof]==0],Htot[data_comb_all.data_type[indprof]==0]/1000,'.-')
ax[0].plot(timeval[data_comb_all.data_type[indprof]==1],Htot[data_comb_all.data_type[indprof]==1]/1000,'.-')
ax[0].set_ylabel('Heat [kJ]')
ax[0].legend(['Monitoring','KivuWatt'],loc='upper left')

ax[1].plot(timeval[data_comb_all.data_type[indprof]==0],Stot[data_comb_all.data_type[indprof]==0]/1000,'.-')
ax[1].plot(timeval[data_comb_all.data_type[indprof]==1],Stot[data_comb_all.data_type[indprof]==1]/1000,'.-')
ax[1].set_ylabel('Salt [tons]')

ax[2].plot(timeval[data_comb_all.data_type[indprof]==0],Mtot[data_comb_all.data_type[indprof]==0]/1000,'.-')
ax[2].plot(timeval[data_comb_all.data_type[indprof]==1],Mtot[data_comb_all.data_type[indprof]==1]/1000,'.-')
ax[2].set_ylabel('Water mass [tons]')

#%% Plot change of salt content due to reinjection
    
boolprof_after=timeval>datetime_extract
indextract_prof=np.where(timeval<=datetime_extract)[0][-1]
S0=np.mean(Slayer_chem[0,indextract_prof:indextract_prof+2]) # kg
#indextract_database=np.where(data_comb_all.time.values.astype('datetime64[s]')<=datetime_extract)[0][-1]
Sal_prof0=np.expand_dims(np.nanmean(data_comb_all.SALIN[:,[indprof[indextract_prof],indprof[indextract_prof+1]]],axis=1),axis=1)
Sal_deep=5.5 # [g/kg], at 350 m according to previous profiles (Schmid et al., 2005)
S_GEP=np.nancumsum(data_flows["Reject"]*Sal_deep) # kg
V_GEP=np.nancumsum(data_flows["Reject"]/tonsh_to_m3s*3600) #m3
indchem=np.where(hypso_z>=np.nanmean(data_comb_all.z_maxdens_smooth[indprof[boolprof_after]]))[0][0]
Achem=np.nanmean(hypso_A[indchem-1:indchem+1])
dh_GEP=V_GEP/Achem # m
#zchem_after=data_comb_all.z_maxdens_smooth.values[indprof[boolprof_after]]
zchem_after=data_comb_all.z_chemfit.values[indprof[boolprof_after]]
zchem_after[zchem_after<250]=np.nan # Remove outlier

fig,ax=plt.subplots(3,1,figsize=(10,5),sharex=True)
hSgrid=ax[0].pcolormesh(timeval[boolprof_after],data_comb_all.depth_interp,data_comb_all.SALIN.values[:,indprof[boolprof_after]]-Sal_prof0,cmap='bwr')
climval=np.nanmax(np.abs(data_comb_all.SALIN.values[:,indprof[boolprof_after]]-Sal_prof0))*np.array([-1,1])
# Cumulative sum of differences (similar):
# hSgrid=ax[0].pcolormesh(timeval[boolprof_after][1:],data_comb_all.depth_interp,np.nancumsum(np.diff(data_comb_all.SALIN.values[:,indprof[boolprof_after]],axis=1),axis=1),cmap='bwr')
# climval=np.nanmax(np.abs(np.nancumsum(np.diff(data_comb_all.SALIN.values[:,indprof[boolprof_after]],axis=1),axis=1)))*np.array([-1,1])
cb=plt.colorbar(hSgrid)
hSgrid.set_clim(climval)
ax[0].plot(timeval[boolprof_after],zchem_after,'-k')
ax[0].plot(timeval[boolprof_after],zchem_after-dz_S,'--k')
cb.set_label('$\Delta S$ [g.kg$^{-1}$]')
ax[0].set_ylim(200,300)
ax[0].invert_yaxis()
ax[0].set_ylabel('Depth [m]')

ax[1].plot(data_flows["Date"],dh_GEP,'-r')
ax[1].plot(timeval[boolprof_after],zchem_after-zchem_after[0],'k-')
ax[1].plot(timeval[np.logical_and(data_comb_all.data_type[indprof]==0,boolprof_after)],zchem_after[data_comb_all.data_type[indprof[boolprof_after]]==0]-zchem_after[0],'.')
ax[1].plot(timeval[np.logical_and(data_comb_all.data_type[indprof]==1,boolprof_after)],zchem_after[data_comb_all.data_type[indprof[boolprof_after]]==1]-zchem_after[0],'.')
_,zafterfit,_=regression_oneline(timeval[boolprof_after].astype(np.int64),zchem_after-zchem_after[0])
ax[1].plot(timeval[boolprof_after],zafterfit,'k--')
ax[1].set_ylabel('$dz_{\\rm chem}$ [m]')

ax[2].plot(data_flows["Date"],S_GEP/1e9,'-r')
ax[2].plot(timeval[boolprof_after],(Slayer_chem[0,boolprof_after]-S0)/1e9,'k-')
ax[2].plot(timeval[np.logical_and(data_comb_all.data_type[indprof]==0,boolprof_after)],(Slayer_chem[0,np.logical_and(data_comb_all.data_type[indprof]==0,boolprof_after)]-S0)/1e9,'.')
ax[2].plot(timeval[np.logical_and(data_comb_all.data_type[indprof]==1,boolprof_after)],(Slayer_chem[0,np.logical_and(data_comb_all.data_type[indprof]==1,boolprof_after)]-S0)/1e9,'.')
_,Safterfit,_=regression_oneline(timeval[boolprof_after].astype(np.int64),(Slayer_chem[0,boolprof_after]-S0)/1e9)
ax[2].plot(timeval[boolprof_after],Safterfit,'k--')
ax[2].set_ylabel('$\Delta M_S$ [Mtons]')

# Same width
ax[1].set_position([ax[1].get_position().x0,ax[1].get_position().y0,ax[0].get_position().width,ax[1].get_position().height]) 
ax[2].set_position([ax[2].get_position().x0,ax[2].get_position().y0,ax[0].get_position().width,ax[2].get_position().height]) 
#%% Plot hourly flow rate
fig,ax=plt.subplots(figsize=(10,5))
ax.plot(data_flows["Date"],data_flows["Reject"]/tonsh_to_m3s)
ax.set_ylabel("Intake [m$^3$.s$^{-1}$]")

#%%

#%% Close datasets
data_gov.close()
data_KW.close()
data_comb.close()
data_comb_periods.close()
data_comb_all.close()