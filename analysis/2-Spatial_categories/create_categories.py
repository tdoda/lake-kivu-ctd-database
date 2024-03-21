# -*- coding: utf-8 -*-
"""
Create databases divided into spatial categories 

@author: T. Doda
"""
import netCDF4
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import path
import pandas as pd
from datetime import datetime, timezone
import math
import cmocean
import seawater as sw 
import geopandas as gpd
from geopy import distance
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *

plt.close ('all')
#%% Database files

database_folder='../1-Extended_database/'
# database_files=["database_combined_260m.nc","database_combined_0m.nc"]
database_files=["database_combined_0m.nc"]
# database_files=["database_combined_260m.nc"]

# Coordinates of GEP    
coord_KW=[29.202352,-2.087932]
coord_KP1=[29.242921,-1.732214]

# Lake contour
lakecontour=gpd.read_file('..\..\..\..\Bathymetry\Kivu_Lake.shp')
path_contour = path.Path(list(lakecontour["geometry"][0].exterior.coords)) 
#%% Create database
for kdata in range(len(database_files)):
    print('***************************************')
    log("Loading data from {}".format(database_files[kdata]))
    #%% Load the data
    nc = netCDF4.Dataset(os.path.join(database_folder, database_files[kdata]), mode='r', format='NETCDF4_CLASSIC')
    gen_att_nc,dim_nc,var_nc,data_nc=extract_dict_netcdf(nc)
    nc.close() 
    
    #%% Remove points outside lake boundaries
    latval=data_nc["latitude"]
    longval=data_nc["longitude"]
    
    coord_CTD=[(longval[kp],latval[kp]) for kp in range(len(latval))]    
    bool_inside=path_contour.contains_points(coord_CTD)
    data_selected=select_data(data_nc,var_nc,'time',np.where(bool_inside==True)[0])
    
    # Export to netCDF
    export_to_netcdf(gen_att_nc,dim_nc,var_nc,data_selected,database_files[kdata][:database_files[kdata].find('.nc')]+"_lake.nc")

    #%% Categorize profile depending on location (for map)
    dist_treshold=2 # km
    lat_north=-1.97 # °
    dist_1ddeg=np.mean(np.array([distance.distance(tuple(coord_KW), (coord_KW[0]+0.1,coord_KW[1])).km,
                        distance.distance(tuple(coord_KW), (coord_KW[0],coord_KW[1]+0.1)).km])) # km/0.1 deg
    dist_prof_to_KW=np.array([np.nan]*len(data_nc["time"]))
    dist_prof_to_KP=np.array([np.nan]*len(data_nc["time"]))
    for kprof in range(len(data_nc["time"])):
        if ~np.isnan(longval[kprof]):
            dist_prof_to_KW[kprof]=distance.distance((longval[kprof],latval[kprof]), tuple(coord_KW)).km
            dist_prof_to_KP[kprof]=distance.distance((longval[kprof],latval[kprof]), tuple(coord_KP1)).km
    bool_closeKW=dist_prof_to_KW<dist_treshold
    bool_closeKP=dist_prof_to_KP<dist_treshold
    bool_north=latval>lat_north
    
    # Export to netCDF
    export_to_netcdf(gen_att_nc,dim_nc,var_nc,
                     select_data(data_nc,var_nc,'time',np.where(bool_closeKW==True)[0]),
                     database_files[kdata][:database_files[kdata].find('.nc')]+"_KW.nc")
    export_to_netcdf(gen_att_nc,dim_nc,var_nc,
                     select_data(data_nc,var_nc,'time',np.where(bool_closeKP==True)[0]),
                     database_files[kdata][:database_files[kdata].find('.nc')]+"_KP.nc")
    export_to_netcdf(gen_att_nc,dim_nc,var_nc,
                     select_data(data_nc,var_nc,'time',np.where(bool_north==True)[0]),
                     database_files[kdata][:database_files[kdata].find('.nc')]+"_north.nc")


