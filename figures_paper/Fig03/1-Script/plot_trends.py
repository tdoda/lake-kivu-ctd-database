# -*- coding: utf-8 -*-
"""
Plot  time series of chemocline drawdown and salt balance.

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
import geopandas as gpd
from shapely.geometry import Point, Polygon
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__),'..', '..','Functions'))
from functions import *
from functions_plot import *


plt.close ('all')
#%% Parameters

database_file_comb="../../../analysis/2-Spatial_categories/database_combined_260m_lake.nc"
# database_file_comb="../../../analysis/2-Spatial_categories/database_combined_260m_KW.nc"


savefig_bool=True
cm = 1/2.54  # [inches/cm]
datetime_extract=datetime(2016,1,1)
date_extract=np.datetime64(datetime_extract)

# Hypsometry
df_hypso=pd.read_csv('../../../analysis/0-Bathymetry/hypsometry_1m.csv',sep=',',names=['z','A'],skiprows=1) 
hypso_z=-df_hypso.z.values
hypso_A=df_hypso.A.values

# Flowrates
file_flows="../../../../../Kivuwatt/Hourly flows 2016-2022.xlsx"
data_flows=pd.read_excel(file_flows,names=["Date","Intake","Reject","Wash","Gas","Consumption","Sweet_flare","Sweet_pilot","Raw_flare","Sweet_net"])
tonsh_to_m3s=1002*3.6 # [(tons/h)/(m3/s)], Conversion factor assuming rho=1002 kg/m^3=1.002 ton/m^3

# Load the data:
data_comb=xr.open_dataset(database_file_comb,decode_times=False)
tnum_val=data_comb.time.values
data_comb["time"]=np.array([datetime.utcfromtimestamp(tnum) for tnum in data_comb.time.data])


col_list=plt.get_cmap('tab10')
xlimval=(datetime(2008,1,1),datetime(2023,1,1))
zlimval=(254,266)

colper=[(0, 0, 0.8),(0.93,0.5,0)]

print('Data loaded!')

#%% Expected drawdown
indchem=np.where(hypso_z>=np.nanmean(data_comb.z_maxdens_smooth[tnum_val<date_extract.astype('datetime64[s]').astype(np.int64)]))[0][0]
Achem=np.nanmean(hypso_A[indchem-1:indchem+1]) # [m2]
drawdown_rate_avg=np.nanmean(data_flows["Reject"]/tonsh_to_m3s/Achem*3600*24*365) # [m/yr]
zchem_GEP=np.nancumsum(data_flows["Reject"]/tonsh_to_m3s/Achem*3600)# [m]

#%% Salt balance
# In specific layers:
# zlayer_top=[232,256] # Based on profiles of salinity trends
# zlayer_bot=[256,280]
zlayer_top=[238,258] # Based on chemocline depth
zlayer_bot=[258,278]
indprof=np.where(np.logical_and(data_comb.max_depth>zlayer_bot[1],data_comb.min_depth<zlayer_top[0]))[0] # Keep profiles with enough data to look at the two layers
H,S,M=compute_balance(data_comb,indprof,hypso_z,hypso_A) # J, kg, kg

timeval=data_comb.time.values[indprof].astype('datetime64[s]') # Rounded seconds
boolprof_after=timeval>datetime_extract

Slayer=np.full((len(zlayer_top),len(indprof)),np.nan)
for kl in range(len(zlayer_top)):
    bool_depth=np.logical_and(hypso_z>=zlayer_top[kl],hypso_z<zlayer_bot[kl])
    Slayer[kl,:]=np.nansum(S[bool_depth,:],axis=0)
    
    
# Above chemocline
# zlayer_bot_chem=data_comb_KW.z_maxdens_smooth.values[indprof]
# Hlayer_chem=np.full((1,len(indprof)),np.nan)
# Slayer_chem=np.full((1,len(indprof)),np.nan)
# Sal_layer=np.full((1,len(indprof)),np.nan) 
# dz_S=20 # [m]
# for kprof in range(len(indprof)):
#     bool_depth=np.logical_and(hypso_z>=zlayer_bot_chem[kprof]-dz_S,hypso_z<zlayer_bot_chem[kprof]) 
#     bool_depthall=np.logical_and(data_comb_KW.depth_interp>=zlayer_bot_chem[kprof]-dz_S,data_comb_KW.depth_interp<zlayer_bot_chem[kprof]) 
#     Hlayer_chem[0,kprof]=np.nansum(H[bool_depth,kprof],axis=0)
#     Slayer_chem[0,kprof]=np.nansum(S[bool_depth,kprof],axis=0)
# # Average salinity in layer [zchem-20,zchem]:
# Sal_layer[0,:]=np.nanmean(data_comb_KW.SALIN[bool_depthall][:,indprof],axis=0)

# Initial salt mass:
indextract_prof=np.where(timeval<=datetime_extract)[0][-1] # end of the pre-extraction period
S0layer_top=np.mean(Slayer[0,indextract_prof:indextract_prof+2]) # kg
S0layer_bot=np.mean(Slayer[1,indextract_prof:indextract_prof+2]) # kg

# Time series of salt mass changes
# Stop_series=(Slayer[0,:]-S0layer_top)/1e9 # tons
# Sbot_series=(Slayer[1,:]-S0layer_bot)/1e9 # tons

Sal_bot=5.7 # [g/kg], at 350 m according to average profiles (Fig. 1)
Sal_top=3.2 # [g/kg], at 240 m according to average profiles (Fig. 1)
salt_rate_avg=np.nanmean(data_flows["Reject"]*(Sal_bot-Sal_top))*24*365*1e-9 # Mtons/yr
S_GEP=np.nancumsum(data_flows["Reject"]*(Sal_bot-Sal_top))# kg

#%% Regression


# 1. Chemocline depth
# pfit_KW,zfit_KW,R2_KW,pcov_KW=regression_period_intersect(data_KW.time.values.astype(np.int64)*1e-9,data_KW.z_maxdens_smooth.values,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
# pfit_north,zfit_north,R2_north,pcov_north=regression_period_intersect(data_north.time.values.astype(np.int64)*1e-9,data_north.z_maxdens_smooth.values,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
pfitz,zfit,R2z,pcovz=regression_period_intersect(tnum_val,data_comb.z_maxdens_smooth.values,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])

# 2. Salt in upper layer
# Forced intercept:
# pfitS,Safterfit,R2S,_=regression_oneline(tnum_val[indprof][boolprof_after],(Slayer[0,boolprof_after]-S0layer_top)/1e9,(tnum_val[indprof][boolprof_after][0],0))
# pfitS_flow,Safterfit_flow,R2S_flow,_=regression_oneline(data_flows["Date"].to_numpy().astype(np.int64)*1e-9,S_GEP/1e9,(tnum_val[indprof][boolprof_after][0],0))

# Free intercept:
# pfitS,Safterfit,R2S,_=regression_oneline(tnum_val[indprof][boolprof_after],(Slayer[0,boolprof_after]-S0layer_top)/1e9)
pfitS_all,Sfit_raw,R2S_all,pcovS=regression_period_intersect(tnum_val[indprof],Slayer[0,:]/1e9,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
pfitS=pfitS_all[1]
R2S=R2S_all[1]
# Compute offset to have MS=0 at the extraction date:
Soffset=np.polyval(pfitS,date_extract.astype('datetime64[s]').astype(np.int64))
Stop_series=Slayer[0,:]/1e9-Soffset # tons
Sfit=Sfit_raw-Soffset
pfitS_flow,Safterfit_flow,R2S_flow,_=regression_oneline(data_flows["Date"].to_numpy().astype(np.int64)*1e-9,S_GEP/1e9)

# 3. Salt in bottom layer
pfitSbot_all,Sbotfit_raw,R2Sbot_all,pcovSbot=regression_period_intersect(tnum_val[indprof],Slayer[1,:]/1e9,datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
pfitSbot=pfitSbot_all[1]
R2Sbot=R2Sbot_all[1]
# Compute offset to have MS=0 at the extraction date:
Sbotoffset=np.polyval(pfitSbot,date_extract.astype('datetime64[s]').astype(np.int64))
Sbot_series=Slayer[1,:]/1e9-Sbotoffset # tons
Sbotfit=Sbotfit_raw-Sbotoffset


#%% Plot time series

fig,ax=plt.subplots(3,1,figsize=(18*cm,15*cm),sharex=True)

# 1. Chemocline depth
ax[0].plot(data_comb.time,data_comb.z_maxdens_smooth,'k-',linewidth=1)
ax[0].plot(data_flows["Date"],zchem_GEP+np.polyval(pfitz[0],data_flows["Date"].values[0].astype('datetime64[s]').astype(np.int64)),'--',color=(0.5,0.5,0.5))
# ax[0].plot(data_KW.time,data_KW.z_maxdens_smooth,'k-',linewidth=1)
# ax[0].plot(data_north.time,data_north.z_maxdens_smooth,'g-',linewidth=1)
ax[0].plot(data_comb.time[data_comb.time<date_extract],zfit[data_comb.time<date_extract],'--',color=colper[0])
ax[0].plot(data_comb.time[data_comb.time>date_extract],zfit[data_comb.time>date_extract],'--',color=colper[1])
# ax[0].plot(data_KW.time,zfit_KW,'--',color=col_list(3))
# ax[0].plot(data_north.time,zfit_north,'--',color=col_list(4))
ax[0].plot([date_extract,date_extract],zlimval,':',color=(0.8,0,0))
ax[0].text(xlimval[0],265,"d$z_{{\\rm chem}}$/d$t$ = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(pfitz[1][0]*3600*24*365,np.sqrt(pcovz[2,2])*3600*24*365,R2z[1]),
            color=colper[1],horizontalalignment='left',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})   
ax[0].text(date_extract,265,"d$z_{{\\rm chem}}$/d$t$ $\\approx$ {:.2f} m/yr".format(drawdown_rate_avg),
            color=(0.5,0.5,0.5),horizontalalignment='left',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2}) 
ax[0].set_xlim(xlimval)
ax[0].set_ylim(zlimval)
ax[0].set_ylabel('$z_{\\rm chem}$ [m]')
ax[0].invert_yaxis()

# 2. Salt in upper layer
ax[1].plot(timeval,Stop_series,'k-',linewidth=1)
ax[1].plot(data_flows["Date"],S_GEP/1e9,'--',color=(0.5,0.5,0.5))
ax[1].plot(data_comb.time[indprof][data_comb.time[indprof]<date_extract],Sfit[data_comb.time[indprof]<date_extract],'--',color=colper[0])
ax[1].plot(data_comb.time[indprof][data_comb.time[indprof]>date_extract],Sfit[data_comb.time[indprof]>date_extract],'--',color=colper[1])
ylimval=ax[1].get_ylim()
ax[1].plot([date_extract,date_extract],ylimval,':',color=(0.8,0,0))
ax[1].set_yticks(np.arange(-10,10,2))
ax[1].set_ylim(ylimval)
ax[1].text(xlimval[0],2.5,"d$M_{{S,{{\\rm top}}}}$/dt = {:.2f}$\\pm${:.2f} Mtons/yr\n $R^2$ = {:.2f}".format(pfitS[0]*3600*24*365,np.sqrt(pcovS[2,2])*3600*24*365,R2S),
          color=colper[1],horizontalalignment='left',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
ax[1].text(date_extract,2,"d$M_{{S,{{\\rm top}}}}$/dt $\\approx$ {:.2f} Mtons/yr".format(salt_rate_avg),
            color=(0.5,0.5,0.5),horizontalalignment='left',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})    
ax[1].set_ylabel('$\Delta M_{S,{\\rm top}}$ [Mtons]')

# 3. Salt in bottom layer
ax[2].plot(timeval,Sbot_series,'k-',linewidth=1)
ax[2].plot(data_comb.time[indprof][data_comb.time[indprof]<date_extract],Sbotfit[data_comb.time[indprof]<date_extract],'--',color=colper[0])
ax[2].plot(data_comb.time[indprof][data_comb.time[indprof]>date_extract],Sbotfit[data_comb.time[indprof]>date_extract],'--',color=colper[1])
ylimval=ax[2].get_ylim()
ax[2].plot([date_extract,date_extract],ylimval,':',color=(0.8,0,0))
ax[2].set_yticks(np.arange(-10,10,2))
ax[2].set_ylim(ylimval)
ax[2].text(xlimval[0],-2.5,"d$M_{{S,{{\\rm bot}}}}$/d$t$ = {:.2f}$\\pm${:.2f} Mtons/yr\n $R^2$ = {:.2f}".format(pfitSbot[0]*3600*24*365,np.sqrt(pcovSbot[2,2])*3600*24*365,R2Sbot),
          color=colper[1],horizontalalignment='left',verticalalignment='top',bbox={"facecolor":"grey","alpha":0.2})   
ax[2].set_ylabel('$\Delta M_{S,{\\rm bot}}$ [Mtons]')




#%% Save figure
if savefig_bool:
    fig.savefig("../2-Figures_raw/Fig03_raw.png",dpi=400)
    fig.savefig("../2-Figures_raw/Fig03_raw.svg")
    print('Figure saved!')

#%% Close datasets
data_comb.close()
