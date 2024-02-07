# -*- coding: utf-8 -*-
"""
Combine all profiles from monitoring program and Kivuwatt separately (one file per data type).

@author: T. Doda
"""
import os
import yaml
import numpy as np
import netCDF4
from datetime import datetime, timezone
from ctd_grid import ctd_grid
from functions import *

#%% Folders
data_folders = ["../data/Level2B_TD/Government/", "../data/Level2B_TD/Kivuwatt/"]
netcdf_files = ["data_gov3.nc", "data_Kivuwatt3.nc"]

with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

if not os.path.exists(directories["Level3_dir"]):
    os.makedirs(directories["Level3_dir"])
    
# # Periods to remove (government):
# dateperiod_rem=[[datetime(2016,1,14,11,0,0),datetime(2016,1,14,12,0,0)],[datetime(2016,2,10,11,0,0),datetime(2016,2,10,14,0,0)],[datetime(2019,9,3,0,0,0),datetime(2019,9,4,0,0)],[datetime(2019,10,28),datetime(2019,10,29)],[datetime(2020,3,17),datetime(2020,3,18)],[datetime(2021,6,3,10,40,0),datetime(2021,6,3,11,0,0)]] # Time limits of the period (density peak, wrong pressue calibration (?), wrong conductivity/temperature)
# tperiod_rem=[None]*len(dateperiod_rem)
# for kperiod in np.arange(len(dateperiod_rem)):
#     tperiod_rem[kperiod]=[dateperiod_rem[kperiod][k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    
#  # Periods to remove (Kivuwatt):   
# dateperiod_rem_KW=[[datetime(2019,11,7,9,0,0),datetime(2019,11,7,10,0,0)],[datetime(2021,6,3),datetime(2021,6,11)]] # Time limits of the period (depth shift, different depth calculation)
# tperiod_rem_KW=[None]*len(dateperiod_rem)
# for kperiod in np.arange(len(dateperiod_rem_KW)):
#     tperiod_rem_KW[kperiod]=[dateperiod_rem_KW[kperiod][k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    
    

for kdata in [0,1]:
# for kdata in [1]:
    print('***************************************')
    log("Loading data from {}".format(data_folders[kdata]))
    #%% Load the data
    
    files = os.listdir(data_folders[kdata])
    files.sort()
    
    first = True
    kfile=0
    data_dict={}
    for file in files:
        kfile=kfile+1
        print('Progress: {:.1f} %'.format(kfile/len(files)*100))
        nc = netCDF4.Dataset(os.path.join(data_folders[kdata], file), mode='r', format='NETCDF4_CLASSIC')
        
        indkeep=np.arange(len(nc.variables["time"][:]))
        # indrem=np.array([])
        # if kdata==0: # Government data: periods to remove    
        #     for kperiod in np.arange(len(dateperiod_rem)):
        #         indrem=np.concatenate((indrem,np.where(np.logical_and(nc.variables["time"][:]>tperiod_rem[kperiod][0],nc.variables["time"][:]<tperiod_rem[kperiod][1]))[0])) 
        # else:
        #     for kperiod in np.arange(len(dateperiod_rem_KW)):
        #         indrem=np.concatenate((indrem,np.where(np.logical_and(nc.variables["time"][:]>tperiod_rem_KW[kperiod][0],nc.variables["time"][:]<tperiod_rem_KW[kperiod][1]))[0]))
        # if len(list(indrem))>0: # not empty
        #     indkeep=np.delete(indkeep,indrem.astype(int))
        varnames=list(nc.variables.keys())
        varnames.remove("depth_interp")
        if first:
            for var in varnames:
                if len(nc.variables[var][:].shape)==1:
                    data_dict[var] = nc.variables[var][indkeep].data 
                else:
                    data_dict[var] =nc.variables[var][:,indkeep].data
            data_dict["depth_interp"] = nc.variables["depth_interp"][:].data 
            
            # data_dict["t"] = nc.variables["time"][indkeep] 
            # data_dict["press"] =nc.variables["Press"][:,indkeep]
            # data_dict["temp"] = nc.variables["Temp"][:,indkeep]
            # data_dict["cond"] = nc.variables["Cond"][:,indkeep]
            # data_dict["turb"] = nc.variables["Turb"][:,indkeep] 
            # data_dict["pH"] = nc.variables["pH"][:,indkeep]
            # data_dict["DO"] = nc.variables["DO_mg"][:,indkeep]
            # data_dict["rho"] = nc.variables["rho"][:,indkeep]   
            first = False
        else:
            for var in varnames:
                if len(nc.variables[var][:].shape)==1:
                    data_dict[var] = np.concatenate((data_dict[var], nc.variables[var][:][indkeep].data), axis=0)
                else:
                    data_dict[var]=np.concatenate((data_dict[var], nc.variables[var][:][:,indkeep].data), axis=1)
            # data_dict["t"] = np.concatenate((data_dict["t"], nc.variables["time"][:][indkeep]), axis=0)
            # data_dict["press"]=np.concatenate((data_dict["press"], nc.variables["Press"][:][:,indkeep]), axis=1)
            # data_dict["temp"] = np.concatenate((data_dict["temp"], nc.variables["Temp"][:][:,indkeep]), axis=1) 
            # data_dict["cond"]= np.concatenate((data_dict["cond"], nc.variables["Cond"][:][:,indkeep]), axis=1) 
            # data_dict["turb"] = np.concatenate((data_dict["turb"], nc.variables["Turb"][:][:,indkeep]), axis=1)
            # data_dict["pH"] = np.concatenate((data_dict["pH"], nc.variables["pH"][:][:,indkeep]), axis=1) 
            # data_dict["DO"] = np.concatenate((data_dict["DO"], nc.variables["DO_mg"][:][:,indkeep]), axis=1)
            # data_dict["rho"] = np.concatenate((data_dict["rho"], nc.variables["rho"][:,indkeep]), axis=1) 
        nc.close()
    
    data_dict["datetime"]=np.array([int(datetime.utcfromtimestamp(k).strftime('%Y%m%d%H%M%S')) for k in data_dict["time"]])
    
    # Add min depth and max depth:
    min_depth=np.array([])
    max_depth=np.array([])
    for kprof in np.arange(len(data_dict["time"])):
        mindepthval=data_dict["depth_interp"][np.where(~np.isnan(data_dict["rho"][:,kprof]))[0][0]]
        maxdepthval=data_dict["depth_interp"][np.where(~np.isnan(data_dict["rho"][:,kprof]))[0][-1]]
        min_depth = np.concatenate((min_depth, np.array([mindepthval])), axis=0)
        max_depth = np.concatenate((max_depth, np.array([maxdepthval])), axis=0)
    data_dict["min_depth"]=min_depth
    data_dict["max_depth"]=max_depth
    #%% Create netCDF file
    grid=ctd_grid()
    
    for var in grid.variables:
        if var in data_dict.keys():
            grid.data[var]=data_dict[var]
        else: 
            if len(grid.variables[var]['dim'])==1:
                grid.data[var]=np.full(data_dict["time"].shape,np.nan)
            else:
                grid.data[var]=np.full(data_dict["Cond"].shape,np.nan)
    grid.to_netcdf(directories["Level3_dir"],netcdf_files[kdata])
                
    
