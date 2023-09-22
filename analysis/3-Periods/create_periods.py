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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *

plt.close ('all')
#%% Database files

database_folder='../2-Spatial_categories/'
database_files=["database_combined2_260m_lake.nc"]


# Periods to average
# year_periods=np.arange(2008,2023,1)
# t0=[datetime(yearval,1,1) for yearval in year_periods] # Yearly periods
# tf=[datetime(yearval+1,1,1) for yearval in year_periods]
t0=[datetime(2009,1,1),datetime(2016,1,1)] # 7 years
tf=[datetime(2016,1,1),datetime(2023,1,1)] # 7 years


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
    prof_avg, prof_std=database_periods.compute_avgprof(data_nc,t0_periods=t0,tf_periods=tf)
    trend_avg,trend_fit,z_iso=database_periods.compute_avgtrend(data_nc,t0_periods=t0,tf_periods=tf,dz=1)
    
    
    #%% Save netCDF 
    database_periods.to_netcdf(database_files[kdata][:database_files[kdata].find('.nc')]+"_"+str(len(t0))+'periods.nc')


# Plot time series isopycnals (to check)
plt.figure()
rhoval=999
indprof=np.where(np.logical_and(database_periods.data["time"]>t0[1].replace(tzinfo=timezone.utc).timestamp(),database_periods.data["time"]<tf[1].replace(tzinfo=timezone.utc).timestamp()))[0]
xval=database_periods.data["time"]/(3600*24*365)
yval=z_iso["rho"][np.where(database_periods.data["rho_trend"]>rhoval)[0][0],:]
pfit,zfit,R2=regression_oneline(xval[indprof],yval[indprof])
plt.plot(xval[indprof],yval[indprof],'.-')
plt.plot(xval[indprof],zfit,'r-')