# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 09:44:13 2023

@author: dodatomy
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
from geopy import distance
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *


#%% Load bathymetry
bathy_data=pd.read_csv('bathymetry_grid_1mdeg_1dobs.csv', sep=",",index_col=0) 
bathy_depth=bathy_data.values
bathy_long=bathy_data.columns.values.astype('float')
bathy_lat=bathy_data.index.values

#%% Hypsometry
dlat=bathy_lat[1]-bathy_lat[0] #[°]
dx_bathy=distance.distance((np.mean(bathy_lat),np.mean(bathy_long)), (np.mean(bathy_lat)+dlat,np.mean(bathy_long))).m
dy_bathy=distance.distance((np.mean(bathy_lat),np.mean(bathy_long)), (np.mean(bathy_lat),np.mean(bathy_long)+dlat)).m
hypso_z,hypso_A=compute_hypso(-bathy_depth,dA=dx_bathy*dy_bathy,dz=1) #m, m^2

#%% Save data
df_hypso=pd.DataFrame({'z [m]':-hypso_z,'A [m2]':np.round(hypso_A)})
df_hypso.to_csv('hypsometry_1m.csv', sep=",")
