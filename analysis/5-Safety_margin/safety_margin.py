# -*- coding: utf-8 -*-
"""
Estimate changes in safety margin by mixing profiles of total gas pressure (initial profile from model).

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

savefig_bool=False

# breakpoint()
plt.close ('all')
#%% Data files
savefig_bool=False

atm_to_bar=1.01325 # bar/atm
data_comb=xr.open_dataset("../2-Spatial_categories/database_combined_260m_lake.nc",decode_times=False)

model_file="..\..\..\..\Model\p26ed350rid240\Analysis_p26ed350rid240_V3.xlsx"
df_model=pd.read_excel(model_file,sheet_name=["pressure"],skiprows=3)
profmod_depth=df_model["pressure"]["Unnamed: 0"].values 
profmod_gasP=df_model["pressure"]["Initial"].values*atm_to_bar # [bar]
# Set it to zero at the surface:
profmod_gasP=profmod_gasP-profmod_gasP[0]
prof_depth=data_comb.depth_interp.values
prof_hydroP=np.nanmean(data_comb.Press.values,axis=1)/10 # [bar]

# Interpolate to depth values:
# profmod_gasP=np.interp(prof_depth,profmod_depth,profmod_gasP,left=np.nan,right=np.nan)
prof_hydroP=np.interp(profmod_depth,prof_depth,prof_hydroP,left=np.nan,right=np.nan)

print('Data loaded!')

#%%
zML_bot=350
zML_topval=np.arange(1,241,1)
pavg_val=np.full(zML_topval.shape,np.nan)
prof_mixed=np.full((len(profmod_depth),len(zML_topval)),np.nan)

for k in range(len(zML_topval)):
    pavg_val[k],prof_mixed[:,k]=create_mixed_layer(profmod_depth,profmod_gasP,zML_bot=zML_bot,zML_top=zML_topval[k])

# Find deepest value of zML_topval that leads to ebullition
ind_limit=np.where(np.interp(profmod_depth,zML_topval,pavg_val,left=np.nan,right=np.nan)>prof_hydroP)[0][-1]
zML_limit=zML_topval[ind_limit]

#%% Quick plot
fig,ax = plt.subplots(1,1,figsize=(6,4))
ax.plot(profmod_gasP,profmod_depth,'-k')
ax.plot(prof_hydroP,profmod_depth,'-r')
ax.plot(pavg_val,zML_topval,'--k')
ax.plot(prof_mixed[:,ind_limit],profmod_depth,'-b')
# ax.plot(prof_mixed[:,np.where(zML_topval==240)[0][0]],profmod_depth,'-g')
ax.set_ylim(0,zML_bot)
ax.invert_yaxis()
ax.legend(["Initial gas pressure (2004)","Absolute pressure","Mixed layer gas pressure","Critical profile"])
ax.set_xlabel("Pressure [bar]")
ax.set_ylabel("Depth [m]")

if savefig_bool:
    fig.savefig("critical_pressure_raw.png",dpi=400)  
    fig.savefig("critical_pressure_raw.svg")  
    print('Figure saved')

#%% Close datasets
data_comb.close()