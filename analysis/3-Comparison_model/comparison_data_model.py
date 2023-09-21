# -*- coding: utf-8 -*-
"""
Compare data with 1D model (Aquasim).

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
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *


plt.close ('all')
#%% Data files
savefig_bool=False

database_files=["database_combined2_260m.nc","database_combined2_260m_2periods.nc","database_combined2_260m_15periods.nc"]
data_comb=xr.open_dataset("../1-Database/"+database_files[0])
data_comb_periods=xr.open_dataset("../1-Database/"+database_files[1],decode_times=False)
data_comb_yr=xr.open_dataset("../1-Database/"+database_files[2],decode_times=False)
date_prof_deep=[datetime.utcfromtimestamp(data_comb.time.values[i].astype(np.int64) * 1e-9) for i in range(len(data_comb.time))]
datetime_periods=[[datetime.utcfromtimestamp(tnum) for tnum in data_comb_yr.time0_periods.values],
                  [datetime.utcfromtimestamp(tnum) for tnum in data_comb_yr.timef_periods.values]]

datetime_extract=datetime(2016,1,1)

model_file="..\..\..\..\Model\p26ed450rid240\Analysis_p26ed450rid240_V3.xlsx"
df_model=pd.read_excel(model_file,sheet_name=["T","S","rho"],skiprows=2)
yearval=[int(yr) for yr in df_model["rho"].columns[1:]]
depthval=df_model["rho"].depth.values[1:]
rhoval=np.full((len(depthval),len(yearval)),np.nan)
tempval=np.full((len(depthval),len(yearval)),np.nan)
salval=np.full((len(depthval),len(yearval)),np.nan)
for kyr in range(len(yearval)):
    tempval[:,kyr]=df_model["T"].values[1:,kyr+1]
    salval[:,kyr]=df_model["S"].values[1:,kyr+1]
    rhoval[:,kyr]=df_model["rho"].values[1:,kyr+1]
    
data_model=[tempval,salval,rhoval]
yr_CTD=[data_comb_yr.meanprof_Temp_avg,data_comb_yr.meanprof_SALIN_avg,data_comb_yr.meanprof_rho_avg]
avg_CTD=[data_comb_periods.meanprof_Temp_avg,data_comb_periods.meanprof_SALIN_avg,data_comb_periods.meanprof_rho_avg]
std_CTD=[data_comb_periods.meanprof_Temp_std,data_comb_periods.meanprof_SALIN_std,data_comb_periods.meanprof_rho_std]
trend_CTD=[data_comb_periods.trendfit_Temp,data_comb_periods.trendfit_SALIN,data_comb_periods.trendfit_rho]
print('Data loaded!')

#%% Compute trends from model
trend_model=[[],[],[]]
trend_total=[[],[],[]]
for kvar in [0,1,2]:
    trend_model[kvar]=np.diff(data_model[kvar],axis=1)/np.diff(yearval)
    trend_total[kvar]=(data_model[kvar][:,-1]-data_model[kvar][:,0])/(yearval[-1]-yearval[0])
    
# Isopycnals displacements
iso_depth=np.full((len(data_comb_periods.rho_trend),len(yearval)),np.nan)


#%% Figure
# ylimval=(0,500)
ylimval=(230,280)
z_chem=np.nanmean(data_comb.z_maxdens[data_comb.z_maxdens>200])

fig,ax=plt.subplots(2,3,figsize=(6,6),sharey=True)
yr1=2015
yr2=2022
ind1=np.where(np.array(datetime_periods[0])>=datetime(yr1,1,1))[0][0]
ind2=np.where(np.array(datetime_periods[0])>=datetime(yr2,1,1))[0][0]
hp=[]
axlabel=["T [°C]","S [g kg$^{-1}$]","$\\rho$ [kg m$^{-3}$]"]

for kvar in [0,1,2]:
    hp1,=ax[0,kvar].plot(data_model[kvar][:,0],depthval,'-r')
    hp2,=ax[0,kvar].plot(data_model[kvar][:,1],depthval,':r')
    hp3,=ax[0,kvar].plot(yr_CTD[kvar][:,ind1],data_comb_periods.depth_interp,'-k') 
    hp4,=ax[0,kvar].plot(yr_CTD[kvar][:,ind2],data_comb_periods.depth_interp,':k') 
    xlimval=ax[0,kvar].get_xlim()
    ax[0,kvar].plot(xlimval,[z_chem]*2,'--',color=[0.5,0.5,0.5])
    ax[0,kvar].set_xlim(xlimval)
    if kvar==0:
        hp=[hp1,hp2,hp3,hp4]
    ax[0,kvar].set_xlabel(axlabel[kvar])
    # ax[0,kvar].plot(avg_CTD[kvar][:,0],data_comb_periods.depth_interp,'-k') 
    # ax[0,kvar].plot(avg_CTD[kvar][:,1],data_comb_periods.depth_interp,':k')  
    
    # ax[0,kvar].fill_betweenx(data_comb_periods.depth_interp, 
    #                        avg_CTD[kvar][:,1]-std_CTD[kvar][:,1], 
    #                        avg_CTD[kvar][:,1]+std_CTD[kvar][:,1],
    #                        color='r',alpha=0.2)
    
    ax[1,kvar].plot(trend_model[kvar][:,0],depthval,'r')
    ax[1,kvar].plot(trend_CTD[kvar][:,1],data_comb_periods.depth_trend,'k')
    ax[1,kvar].plot([0,0],ylimval,'-',color=[0.5,0.5,0.5])
    xlimval=ax[1,kvar].get_xlim()
    ax[1,kvar].plot(xlimval,[z_chem]*2,'--',color=[0.5,0.5,0.5])
    ax[1,kvar].set_xlim(xlimval)
    #ax[1,kvar].plot(trend_total[kvar],depthval,'r')

ax[1,0].set_xlabel('T trend [°C.yr$^{-1}$]')
ax[1,0].set_ylabel('Depth [m]')
ax[1,1].set_xlabel('S trend [g.kg$^{-1}$.yr$^{-1}$]')
ax[1,2].set_xlabel('$\\rho$ trend [kg.m$^{-3}$.yr$^{-1}$]')

ax[0,0].set_ylabel('Depth [m]')
ax[0,0].set_ylim(ylimval)
ax[0,0].invert_yaxis()
ax[0,0].legend(hp,["Model initial","Model + 10 years","Obs initial (2015)","Obs + 7 yrs (2022)"])
fig.set_tight_layout(True)

if savefig_bool:
    fig.savefig("Figures/trend_model_CTD_"+str(ylimval[0])+"_"+str(ylimval[1])+".png",dpi=400)  
    fig.savefig("Figures/trend_model_CTD"+str(ylimval[0])+"_"+str(ylimval[1])+".svg")  
    print('Figure saved')

#%% Close datasets
data_comb.close()
data_comb_periods.close()
