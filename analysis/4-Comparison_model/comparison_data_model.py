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
import seawater as sw
from scipy.stats.distributions import  t
from scipy.interpolate import interp1d
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *

# breakpoint()
plt.close ('all')
#%% Data files
savefig_bool=False

database_files=["database_combined_260m_lake.nc","database_combined_260m_lake_2periods.nc","database_combined_260m_lake_15periods.nc"]
data_comb=xr.open_dataset("../2-Spatial_categories/"+database_files[0],decode_times=False)
data_comb["time"]=np.array([datetime.utcfromtimestamp(tnum) for tnum in data_comb.time.data])
data_comb_periods=xr.open_dataset("../3-Periods/"+database_files[1],decode_times=False)
data_comb_year=xr.open_dataset("../3-Periods/"+database_files[2],decode_times=False)
date_prof_deep=[datetime.utcfromtimestamp(data_comb.time.values[i].astype(np.int64) * 1e-9) for i in range(len(data_comb.time))]
datetime_periods=[[datetime.utcfromtimestamp(tnum) for tnum in data_comb_year.time0_periods.values],
                  [datetime.utcfromtimestamp(tnum) for tnum in data_comb_year.timef_periods.values]]

datetime_extract=datetime(2016,1,1)

model_file="..\..\..\..\Model\p26ed350rid240_2004_2014\Results_S_T_rho.xlsx"
df_model=pd.read_excel(model_file,sheet_name=["T","S","rho"],skiprows=2)
yearval=[int(yr) for yr in df_model["rho"].columns[1:]]
tval=np.array([datetime(yeari,1,1).replace(tzinfo=timezone.utc).timestamp() for yeari in yearval])
depthval=df_model["rho"].depth.values
rhoval=np.full((len(depthval),len(yearval)),np.nan)
tempval=np.full((len(depthval),len(yearval)),np.nan)
salval=np.full((len(depthval),len(yearval)),np.nan)
for kyr in range(len(yearval)):
    tempval[:,kyr]=df_model["T"].values[:,kyr+1]
    salval[:,kyr]=df_model["S"].values[:,kyr+1]
    rhoval[:,kyr]=df_model["rho"].values[:,kyr+1]
    
# Add longterm simulations:
model_file2="..\..\..\..\Model\p26ed350rid240\Analysis_p26ed350rid240_V3.xlsx"
df_model2=pd.read_excel(model_file2,sheet_name=["T","S","rho"],skiprows=2)
yearval2=[int(yr) for yr in df_model2["rho"].columns[3:]]
tval2=np.array([datetime(yeari,1,1).replace(tzinfo=timezone.utc).timestamp() for yeari in yearval2])
rhoval2=np.full((len(depthval),len(yearval2)),np.nan)
tempval2=np.full((len(depthval),len(yearval2)),np.nan)
salval2=np.full((len(depthval),len(yearval2)),np.nan)
for kyr in range(len(yearval2)):
    tempval2[:,kyr]=df_model2["T"].values[1:,kyr+3]
    salval2[:,kyr]=df_model2["S"].values[1:,kyr+3]
    rhoval2[:,kyr]=df_model2["rho"].values[1:,kyr+3]
    
# Concatenate data
yearval=np.concatenate((yearval,yearval2),axis=0)
tval=np.concatenate((tval,tval2),axis=0)
rhoval=np.concatenate((rhoval,rhoval2),axis=1)
tempval=np.concatenate((tempval,tempval2),axis=1)
salval=np.concatenate((salval,salval2),axis=1)
    
#%% Load hypsometry
df_hypso=pd.read_csv('../0-Bathymetry/hypsometry_1m.csv',sep=',',names=['z','area'],skiprows=1) 
    
# Compute N2 from model:
N2model=compute_N2(depthval,rhoval,windowsize=10,g=9.81)

# Comput St from model:
_,Sc_Imb_tot=compute_Sc(depthval,rhoval,np.full(tval.shape,depthval[0]),
    np.full(tval.shape,depthval[-1]),hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=2,zmax=300,g=sw.g(lat=-2))
_,Sc_Imb_230_280=compute_Sc(depthval,rhoval,np.full(tval.shape,depthval[0]),
    np.full(tval.shape,depthval[-1]),hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=230,zmax=280,g=sw.g(lat=-2),layer_specific=True)
_,Sc_Imb_78_280=compute_Sc(depthval,rhoval,np.full(tval.shape,depthval[0]),
    np.full(tval.shape,depthval[-1]),hypso_z=-df_hypso['z'].values,hypso_A=df_hypso['area'].values,zmin=78,zmax=280,g=sw.g(lat=-2),layer_specific=True)

    
data_model=[tempval,salval,rhoval,N2model]
# yr_CTD=[data_comb_year.meanprof_Temp_avg,data_comb_year.meanprof_SALIN_avg,data_comb_year.meanprof_rho_avg]
# avg_CTD=[data_comb_periods.meanprof_Temp_avg,data_comb_periods.meanprof_SALIN_avg,data_comb_periods.meanprof_rho_avg]
# std_CTD=[data_comb_periods.meanprof_Temp_std,data_comb_periods.meanprof_SALIN_std,data_comb_periods.meanprof_rho_std]
# trend_CTD=[data_comb_periods.trendfit_Temp,data_comb_periods.trendfit_SALIN,data_comb_periods.trendfit_rho]
print('Data loaded!')

#%% Compute trends from model (for temp, salin, rho and N2)
trend_fit_model=[[],[],[],[]]
trend_avg_model=[[],[],[],[]]
nyear=7 # Number of years used to compute trend (doesn't include the initial year)

for kvar in [0,1,2,3]:  
    if nyear>data_model[kvar].shape[1]-1:
        raise Exception('Number of years is too large for the dataset')
    trend_avg_model[kvar]=(data_model[kvar][:,nyear]-data_model[kvar][:,0])/(yearval[nyear-1]-yearval[0])
    
    trend_fit_model[kvar]=np.full((len(depthval),),np.nan) # Profile of trends
    
    for kz in range(len(depthval)): 
        if np.sum(~np.isnan(data_model[kvar][kz,:nyear+1]))>2:
            pfit,_,_=regression_oneline(tval[:nyear+1]/(3600*24*365),data_model[kvar][kz,:nyear+1])
            trend_fit_model[kvar][kz]=pfit[0]

#%% Compute isopycnals displacements from model (for temp, salin and rho) over n years

modeltrend_iso_avg_all=[]
modeltrend_iso_fit_all=[]
modelvartrend=[]
dvar=[0.001,0.001,0.001]
varnames=["Temp","SALIN","rho"]
for kvar in range(len(varnames)):
    print("Computation of displacements for "+varnames[kvar])
    trend_iso_avg,trend_iso_fit,z_iso,var_trend=compute_iso_displacements(tval[:nyear+1],depthval,data_model[kvar][:,:nyear+1],dvar[kvar],delta_smooth=1,zmin=0,nmin=2,mindur=1)
    modeltrend_iso_avg_all.append(trend_iso_avg)
    modeltrend_iso_fit_all.append(trend_iso_fit)
    modelvartrend.append(var_trend)

#%% Average N2 from model
N2avg=np.nanmean(N2model[:,:nyear+1],axis=1)
N2std=np.nanstd(N2model[:,:nyear+1],axis=1)

#%% Export to netCDF
gen_att_nc = {
    "institution": "Eawag",
    "history": "See history on Renku",
    "conventions": "CF 1.7",
    "title": "Comparison of profiles and trends between model (Aquasim) and observations in Lake Kivu",
}

dim_nc = {
    "tval": {'dim_name': 'time_model', 'dim_size': None},
    "depth_model": {'dim_name': 'depth_model', 'dim_size': None},
    "temp_trend_model": {'dim_name': "temp_trend_model", 'dim_size': None},
    "salin_trend_model": {'dim_name': "salin_trend_model", 'dim_size': None},
    "rho_trend_model": {'dim_name': "rho_trend_model", 'dim_size': None},
}

var_nc = {
    'time_model': {'var_name': 'time_model', 'dim': ('time_model',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'Time of each profile from the model'},
    "depth_model": {'var_name': "depth_model", 'dim': ('depth_model',), 'unit': 'm', 'longname': "Depth from the model"},
    
    "Temp_model":{'var_name': "Temp_model", 'dim': ('depth_model','time_model'), 'unit': 'degC', 'longname': "Temperature from the model"},
    "trendavg_Temp_model":{'var_name': "trendavg_Temp_model", 'dim': ('depth_model',), 'unit': 'degC.yr-1', 'longname': "Average temperature trend from the model"},
    "trendfit_Temp_model":{'var_name': "trendfit_Temp_model", 'dim': ('depth_model',), 'unit': 'degC.yr-1', 'longname': "Temperature trend from linear fit from the model"},
    "temp_trend_model":{'var_name': "temp_trend_model", 'dim': ('temp_trend_model'), 'unit': 'degC', 'longname': "Temperature values for isotherms displacements"},
    "trendavg_iso_Temp_model":{'var_name': "trendavg_iso_Temp_model", 'dim': ('temp_trend_model',), 'unit': 'm.yr-1', 'longname': "Average isotherms displacements"},
    "trendfit_iso_Temp_model":{'var_name': "trendfit_iso_Temp_model", 'dim': ('temp_trend_model',), 'unit': 'm.yr-1', 'longname': "Isotherms displacements from linear fit"},
       
    "SALIN_model":{'var_name': "SALIN_model", 'dim': ('depth_model','time_model'), 'unit': 'g.kg-1', 'longname': "Salinity from the model"},
    "trendavg_SALIN_model":{'var_name': "trendavg_SALIN_model", 'dim': ('depth_model',), 'unit': 'g.kg-1.yr-1', 'longname': "Average salinity trend from the model"},
    "trendfit_SALIN_model":{'var_name': "trendfit_SALIN_model", 'dim': ('depth_model',), 'unit': 'g.kg-1.yr-1', 'longname': "Salinity trend from linear fit from the model"},
    "salin_trend_model":{'var_name': "salin_trend_model", 'dim': ('salin_trend_model'), 'unit': 'g.kg-1', 'longname': "Salinity values for isohalines displacements"},
    "trendavg_iso_SALIN_model":{'var_name': "trendavg_iso_SALIN_model", 'dim': ('salin_trend_model',), 'unit': 'm.yr-1', 'longname': "Average isohalines displacements"},
    "trendfit_iso_SALIN_model":{'var_name': "trendfit_iso_SALIN_model", 'dim': ('salin_trend_model',), 'unit': 'm.yr-1', 'longname': "Isohalines displacements from linear fit"},
    
    "rho_model":{'var_name': "rho_model", 'dim': ('depth_model','time_model'), 'unit': 'kg.m-3', 'longname': "Density from the model"},
    "trendavg_rho_model":{'var_name': "trendavg_rho_model", 'dim': ('depth_model',), 'unit': 'g.kg-1.yr-1', 'longname': "Average density trend from the model"},
    "trendfit_rho_model":{'var_name': "trendfit_rho_model", 'dim': ('depth_model',), 'unit': 'g.kg-1.yr-1', 'longname': "Density trend from linear fit from the model"},
    "rho_trend_model":{'var_name': "rho_trend_model", 'dim': ('rho_trend_model'), 'unit': 'g.kg-1', 'longname': "Density values for isopycnals displacements"},
    "trendavg_iso_rho_model":{'var_name': "trendavg_iso_rho_model", 'dim': ('rho_trend_model',), 'unit': 'm.yr-1', 'longname': "Average isopycnals displacements"},
    "trendfit_iso_rho_model":{'var_name': "trendfit_iso_rho_model", 'dim': ('rho_trend_model',), 'unit': 'm.yr-1', 'longname': "Isopycnals displacements from linear fit"},  
    
    "N2_model":{'var_name': "N2_model", 'dim': ("depth_model","time_model"), 'unit': 's-2', 'longname': "Squared buoyancy frequency"}, 
    "N2avg":{'var_name': "N2_model_avg", 'dim': ("depth_model",), 'unit': 's-2', 'longname': "Averaged squared buoyancy frequency over "+str(nyear)+" yr"}, 
    "N2std":{'var_name': "N2_model_std", 'dim': ("depth_model",), 'unit': 's-2', 'longname': "Squared buoyancy frequency std over "+str(nyear)+" yr"}, 
    "trendavg_N2_model":{'var_name': "trendavg_N2_model", 'dim': ('depth_model',), 'unit': 's-2.yr-1', 'longname': "Average N2 trend from the model"},
    "trendfit_N2_model":{'var_name': "trendfit_N2_model", 'dim': ('depth_model',), 'unit': 's-2.yr-1', 'longname': "N2 trend from linear fit from the model"},
    
    "Sc_Imb_tot":{'var_name':"Sc_Imb_tot_model", 'dim': ("time_model",), 'unit': 'J', 'longname': "Schmidt stability with respect to center of volume and mixed profile"}, 
    "Sc_Imb_230_280":{'var_name':"Sc_Imb_230_280_model", 'dim': ("time_model",), 'unit': 'J', 'longname': "Schmidt stability with respect to center of volume and mixed profile (layer 230-280 m)"}, 
    "Sc_Imb_78_280":{'var_name':"Sc_Imb_78_280_model", 'dim': ("time_model",), 'unit': 'J', 'longname': "Schmidt stability with respect to center of volume and mixed profile (layer 78-280 m)"}, 
    }

data_selected={
    "time_model":tval,
    "depth_model":depthval}

for kvar in range(len(varnames)):
    data_selected[varnames[kvar]+"_model"]=data_model[kvar]
    data_selected["trendavg_"+varnames[kvar]+"_model"]=trend_avg_model[kvar]
    data_selected["trendfit_"+varnames[kvar]+"_model"]=trend_fit_model[kvar]
    data_selected[varnames[kvar].lower()+"_trend_model"]=modelvartrend[kvar]
    data_selected["trendavg_iso_"+varnames[kvar]+"_model"]=modeltrend_iso_avg_all[kvar]
    data_selected["trendfit_iso_"+varnames[kvar]+"_model"]=modeltrend_iso_fit_all[kvar]
data_selected["N2_model"]=N2model
data_selected["N2avg"]=N2avg
data_selected["N2std"]=N2std
data_selected["trendavg_N2_model"]=trend_avg_model[3]
data_selected["trendfit_N2_model"]=trend_fit_model[3]
data_selected["Sc_Imb_tot"]=Sc_Imb_tot
data_selected["Sc_Imb_230_280"]=Sc_Imb_230_280
data_selected["Sc_Imb_78_280"]=Sc_Imb_78_280
export_to_netcdf(gen_att_nc,dim_nc,var_nc,data_selected,"trends_model.nc")

del yearval,tval,rhoval,tempval,salval
#%% Close datasets
data_comb.close()
data_comb_periods.close()
data_comb_year.close()