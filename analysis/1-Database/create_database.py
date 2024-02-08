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
from ctd_database import ctd_database
import seawater as sw 
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *

plt.close ('all')
#%% Data files
data_folder = "../../data/Level3_TD/"
#hypsometry_file='../../../../Bathymetry/Bathymetry_Baerenbold2022.dat'
hypsometry_file='../0-Bathymetry/hypsometry_1m.csv'
data_files = ["data_gov3.nc", "data_Kivuwatt3.nc"]
# data_files = ["data_gov2.nc", "data_Kivuwatt2.nc"]

dmin=260 # Minimum depth of the profiles

# Periods to remove (government):
dateperiod_rem=[[datetime(2016,1,14,11,0,0),datetime(2016,1,14,12,0,0)],[datetime(2016,2,10,11,0,0),datetime(2016,2,10,14,0,0)],[datetime(2019,9,3,0,0,0),datetime(2019,9,4,0,0)],[datetime(2019,10,28),datetime(2019,10,29)],[datetime(2020,3,17),datetime(2020,3,18)],[datetime(2021,6,3,10,40,0),datetime(2021,6,3,11,0,0)]] # Time limits of the period (density peak, wrong pressue calibration (?), wrong conductivity/temperature)
tperiod_rem=[None]*len(dateperiod_rem)
for kperiod in np.arange(len(dateperiod_rem)):
    tperiod_rem[kperiod]=[dateperiod_rem[kperiod][k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    
 # Periods to remove (Kivuwatt):   
dateperiod_rem_KW=[[datetime(2019,11,7,9,0,0),datetime(2019,11,7,10,0,0)],[datetime(2021,6,3),datetime(2021,6,11)]] # Time limits of the period (depth shift, different depth calculation)
tperiod_rem_KW=[None]*len(dateperiod_rem)
for kperiod in np.arange(len(dateperiod_rem_KW)):
    tperiod_rem_KW[kperiod]=[dateperiod_rem_KW[kperiod][k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    
    
tperiod_rem_all=[tperiod_rem,tperiod_rem_KW]
output_files=["database_gov_"+str(dmin)+"m.nc","database_Kivuwatt_"+str(dmin)+"m.nc"]
databases_all=[]
#%% Load hypsometry
df_hypso=pd.read_csv(hypsometry_file,sep=',',names=['z','area'],skiprows=1) 
#df_hypso=df_hypso.loc[df_hypso["z"]<=0,:]
#%% Create database
for kdata in [0,1]:
    print('***************************************')
    log("Loading data from {}".format(data_files[kdata]))
    #%% Load the data
    
    database=ctd_database() 
    # database_periods=ctd_periods()    
    nc = netCDF4.Dataset(os.path.join(data_folder, data_files[kdata]), mode='r', format='NETCDF4_CLASSIC')
    profkeep=nc.variables["max_depth"][:]>=dmin
    tval=nc.variables["time"][:]
    profremove=np.full(profkeep.shape,False)
    for kp in range(len(tperiod_rem_all[kdata])):
        profremove+=np.logical_and(tval>tperiod_rem[kp][0],tval<tperiod_rem[kp][1]) # True if profile was taken during period to remove
    profkeep=np.logical_and(profkeep,~profremove)
    
    #%% Create all variables
    log("Creating variables...")
    for var in database.variables:
        log('Variable '+var,indent=1)
        if var in nc.variables: # Variables from netCDF input file
            if len(nc.variables[var][:].shape)==1: 
                if nc.variables[var][:].shape[0]==len(profkeep): # Same dimension
                    database.data[var]=nc.variables[var][profkeep].data
                else:
                    database.data[var]=nc.variables[var][:].data   
            else:
                database.data[var]=nc.variables[var][:].data[:,profkeep] # Faster than applying .data at the end
        else: # Set to NaN for variables that are not present in netCDF file
            if len(database.variables[var]['dim'])==1:
                database.data[var]=np.full(nc.variables["time"][profkeep].shape,np.nan)
            else:
                database.data[var]=np.full(nc.variables["Cond"][:,profkeep].shape,np.nan)
       
    #%% Compute other variables 
    log("Computing additional variables...")
    database.data["data_type"]=np.full(len(nc.variables["time"][profkeep]),kdata)
    database.compute_maxdens()
    database.compute_metalimnion()
    database.compute_chemfit()
    database.compute_centermass()
    N2=database.compute_N2_database(g=sw.g(lat=-2))
    Sc1,Sc2=database.compute_Sc_database(hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=2,zmax=300,g=sw.g(lat=-2))
    Sc_chemocline1,Sc_chemocline2=database.compute_Sc_database(hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=230,zmax=280,g=sw.g(lat=-2),layer_specific=True,name_layer="_230_280")
    _,_=database.compute_Sc_database(hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=100,zmax=280,g=sw.g(lat=-2),layer_specific=True,name_layer="_100_280")
    _,_=database.compute_Sc_database(hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=78,zmax=280,g=sw.g(lat=-2),layer_specific=True,name_layer="_78_280")
    #database.compute_centermass(hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values)
    # prof_avg, prof_trend1,prof_trend2=database_periods.compute_avgprof_3p(database)
    
    # Periods to average
    # prof_avg, prof_std=database_periods.compute_avgprof(database,t0_periods=t0,tf_periods=tf)
    # trend_avg,trend_fit=database_periods.compute_avgtrend(database,t0_periods=t0,tf_periods=tf,dz=1)
    #database.compute_stratification_pylake(lat=-2,deptha=-df_hypso["z"].values,area=df_hypso["area"].values)
    nc.close() 
    
    
    #%% Plot 1: profiles of temp, cond, dens
    fig,ax=plt.subplots(1,3,figsize=(10,5),sharey=True)
    colval=plt.get_cmap('viridis',len(database.data["time"]))
    for kprof in np.arange(len(database.data["time"])):
        ax[0].plot(database.data["Temp"][:,kprof],database.data["depth_interp"],
                color=colval(kprof))
        
        ax[1].plot(database.data["Cond"][:,kprof],database.data["depth_interp"],
                color=colval(kprof))
        
        ax[2].plot(database.data["rho"][:,kprof],database.data["depth_interp"],
                color=colval(kprof))
    
    ax[0].invert_yaxis()
    ax[0].set_ylabel('Depth [m]')
    ax[0].set_xlabel('Temp [°C]')
    #ax[1].legend(handles=[hplots_all[i] for i in  indselect],labels=[date_prof[i].year for i in  indselect],fontsize=8,loc='upper right')
    ax[1].set_xlabel('Cond [mS.cm$^{-1}$]')
    ax[2].set_xlabel('$\\rho$ [kg.m$^{-3}$]')
    
    #%% Plot 2: profiles of dens and chemocline depth
    fig,ax=plt.subplots(1,1,figsize=(10,3))
    chemodepth=database.data["z_maxdens_smooth"]
    rhochem=[np.nan]*len(database.data["time"])
    for kprof in np.arange(len(database.data["time"])): 
        ax.plot(database.data["rho"][:,kprof]+0.1*kprof,database.data["depth_interp"],'-k')
        if not np.isnan(chemodepth[kprof]):
            rhochem[kprof]=database.data["rho"][np.where(database.data["depth_interp"]>=chemodepth[kprof])[0][0],kprof]+0.1*kprof
    ax.plot(rhochem,chemodepth,'.-r')
    ax.plot(rhochem,database.data["z_meta_middle"],'.-g')
    #ax.plot(rhochem,database.data["z_maxdens"],'.-b')
    ax.plot(rhochem,database.data["z_middens"],'.-m')
    ax.plot(rhochem,database.data["z_chemfit"],'.-b')
    ax.invert_yaxis()
    ax.set_ylabel('Depth [m]')
    ax.set_xlabel('$\\rho$ [kg.m$^{-3}$]')
    #%% Save netCDF 
    database.to_netcdf(output_files[kdata])
    # database_periods.to_netcdf(output_files[kdata][:output_files[kdata].find('.nc')-1]+"_"+str(len(t0))+'periods.nc')
    databases_all.append(database)
#%% Combine databases
print('***************************************')
database_comb=ctd_database()
# database_periods_comb=ctd_periods()

time_comb=np.concatenate((databases_all[0].data["time"],databases_all[1].data["time"]),axis=0)
indsort=time_comb.argsort()
database_comb.data["time"]=time_comb[indsort]
database_comb.data["depth_interp"]=databases_all[0].data["depth_interp"]
database_comb.data["z_bounds"]=databases_all[0].data["z_bounds"]

for var in databases_all[0].variables:
    if var in ['time','depth_interp','z_bounds']:
        continue
    if len(databases_all[0].data[var].shape)==1:
        axisval=0
    else:
        axisval=1
    var_comb=np.concatenate((databases_all[0].data[var],databases_all[1].data[var]),axis=axisval)
    
    if axisval==0:
        database_comb.data[var]=var_comb[indsort]
    else:
        database_comb.data[var]=var_comb[:,indsort]

# Period database
# database_periods_comb.compute_avgprof(database_comb,t0_periods=t0,tf_periods=tf)
# trend_avg,trend_fit=database_periods_comb.compute_avgtrend(database_comb,t0_periods=t0,tf_periods=tf,dz=1)
  
# Save netCDF   
database_comb.to_netcdf("database_combined_"+str(dmin)+"m.nc")
# database_periods_comb.to_netcdf("database_combined_"+str(dmin)+"m_"+str(len(t0))+"periods.nc")


