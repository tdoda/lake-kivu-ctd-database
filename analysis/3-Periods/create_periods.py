# -*- coding: utf-8 -*-
"""
Compute average profiles and trends during specific periods

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
from ctd_periods import ctd_periods
import seawater as sw 
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..','Functions'))
from functions import *

plt.close ('all')
#%% Database files

database_folder='../2-Spatial_categories/'
database_files=["database_combined_260m_lake.nc"]




# Periods to average
# 1) Yearly averaged:
year_periods=np.arange(2008,2023,1)
t0=[datetime(yearval,1,1) for yearval in year_periods] # Yearly periods
tf=[datetime(yearval+1,1,1) for yearval in year_periods]
min_period_trend=0.5 # yr, minimum duration of the dataset to compute trend

# 2) Two periods
# t0=[datetime(2009,1,1),datetime(2016,1,1)] # 7 years
# tf=[datetime(2016,1,1),datetime(2023,1,1)] # 7 years
# min_period_trend=2 # yr


#%% Create database
for kdata in range(len(database_files)):
    print('***************************************')
    log("Loading data from {}".format(database_files[kdata]))
    #%% Load the data
    nc = netCDF4.Dataset(os.path.join(database_folder, database_files[kdata]), mode='r', format='NETCDF4_CLASSIC')
    data_nc=extract_data_netcdf(nc)
    nc.close() 

    #%% Periods to average
    database_periods=ctd_periods()
    prof_avg, prof_std=database_periods.compute_avgprof(data_nc,t0_periods=t0,tf_periods=tf,varnames=["Temp","Cond","SALIN","rho","N2"])
    trend_avg,trend_fit,z_iso=database_periods.compute_avgtrend(data_nc,t0_periods=t0,tf_periods=tf,dz=1,mindur=min_period_trend,dvar=[0.001,0.001,0.001,0.001,1e-5],varnames=["Temp","Cond","SALIN","rho","N2"])
    database_periods.zchem(data_nc)
    
    #%% Save netCDF 
    database_periods.to_netcdf(database_files[kdata][:database_files[kdata].find('.nc')]+"_"+str(len(t0))+'periods.nc')

#%% Plot grid of position z_iso (to check)
xval=database_periods.data["time"]/(3600*24*365)

varname="rho"
plt.figure()
plt.pcolormesh(xval,database_periods.data[varname.lower()+"_trend"],z_iso[varname])

ind_select=np.where(xval>46.3)[0][0]
# ind_select=np.where(xval<46.2)[0][-1]
fig,ax=plt.subplots(1,2)
ax[0].plot(data_nc[varname][:,ind_select],data_nc["depth_interp"])
ax[0].invert_yaxis()

ax[1].plot(z_iso[varname][:,ind_select],database_periods.data[varname.lower()+"_trend"])
#%% Plot time series isopycnals (to check)
# varname="Temp"
# indper=0
# plt.figure()
# # First value with trend:
# indval=np.where(~np.isnan(database_periods.data["trendfit_iso_"+varname][:,indper]))[0][0]
# isoval=database_periods.data[varname.lower()+"_trend"][indval]
# # isoval=23.2
# indprof=np.where(np.logical_and(database_periods.data["time"]>t0[indper].replace(tzinfo=timezone.utc).timestamp(),database_periods.data["time"]<tf[indper].replace(tzinfo=timezone.utc).timestamp()))[0]
# yval=z_iso[varname][np.where(database_periods.data[varname.lower()+"_trend"]>=isoval)[0][0],:]
# pfit,zfit,R2=regression_oneline(xval[indprof],yval[indprof])
# plt.plot(xval[indprof],yval[indprof],'.-')
# plt.plot(xval[indprof],zfit,'r-')