"""
main_ctd_database.py

Create the database from raw CTD profiles, with one final file for REMA profiles 
and one file for Kivuwatt profiles.

Author: T. Doda
Date: 19.03.24

"""
#%%

# -*- coding: utf-8 -*-
import os
import yaml
from ctd import ctd
from datetime import datetime, timezone
import numpy as np
import copy
import time
import pandas as pd

#%% Choices for the database creation

show_output=False # To print the different steps in the console with the log function
save_csv=False # To save the data of L2A and L2B as csv files in addition to netCDF files


#%% Parameters
lake_info = {"lat": -2, "alt": 1462} # Latitude [°] and altitude [m]
lake_level = "../data/lake_level/c_gls.json" # File containing the lake level data

# Import the name of directories:
with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader) 

# Create the directories if not existing:
for directory in directories.values(): 
    if not os.path.exists(directory):
        os.makedirs(directory)

# List of datafiles to read:
# files_REMA=[f for f in os.listdir(directories["Level0_dir"]) if f.endswith((".TOB",".cnv")) ]
files_REMA=['SA241437_6.TOB','SA241437_8.TOB','SBE19plus_01907894_2020_11_02_0002.cnv','081016_5.TOB']
files_REMA.sort()
# files_KW=[f for f in os.listdir(directories["Level0_KW_dir"]) if f.endswith((".csv")) ]
files_KW=['Data1.csv']
files_KW.sort()
files=files_REMA+files_KW
data_type=[0]*len(files_REMA)+[1]*len(files_KW) # Data type = 0 for REMA and = 1 for KW
data_type_name=["REMA","Kivuwatt"]
failed = []

# Files with several profiles (to divide manually):
files_severalprof=['SA241437_6.TOB','SA241437_8.TOB']
indstart=[[1004,3719,10031],[1096,6352,12450]]
indend=[[3718,9165,14210],[5090,10250,15603]]


# Files with data to remove manually:
files_datarem=['SBE19plus_01907894_2020_11_02_0002.cnv']
indrem=[[15194]]

# # Period to remove:
# dateperiod_rem=[] # Time limits of the period
# tperiod_rem=[dateperiod_rem[k].replace(tzinfo=timezone.utc).timestamp() for k in np.arange(len(dateperiod_rem))]

# Kivuwatt profiles with conductivity in mS/mm (profile indices corresponds to the first column of the datafile):
indprof_mSmm=np.arange(23,30,1)

# Profiles with different conversion pressure-depth (profile indices corresponds to the first column of the datafile):
indprof_noconv_depth=np.arange(562,572,1)

# Metadata for Kivuwatt profiles:
CTD_metaKW = ctd(printlog=show_output)
CTD_metaKW.extract_meta_data_Kivuwatt(os.path.join(directories["Level0_KW_dir"], 'Metadata.csv'))

# Load gas data
df_gas=pd.read_excel('..\data\gas_profile\Gas_profile.xlsx',names=['Depth','CH4','CH4_err','CO2','CO2_err'])


#%% Data extraction

start_time=time.time() # current time
index_file=-1

for file in files:
    index_file=index_file+1
    print('********************************')
    
    if index_file==10:
        end_time=time.time()
        time_prof=(end_time-start_time)/10 # time needed to process one profile [s]
    if index_file>=10:
        time_rem=(len(files)-index_file-1)*time_prof/60 # Remaining time [min]
        print('File {}/{} ({}%): {}. Time remaining: {:.1f} min'.format(index_file+1,len(files),round((index_file+1)/len(files)*100),data_type_name[data_type[index_file]],time_rem))
    else:
        print('File {}/{} ({}%): {}'.format(index_file+1,len(files),round((index_file+1)/len(files)*100),data_type_name[data_type[index_file]]))
        
    if data_type[index_file]==1: # Kivuwatt profiles
        try:
            df_KW=pd.read_csv(os.path.join(directories["Level0_KW_dir"], file),encoding='ISO-8859-1',sep=',',
                            header=0,names=['Profile','Hour','Press','Depth_KW','Temp','Cond'],dtype={'Time':str})
            n_subprof=len(np.unique(df_KW["Profile"].values))
            CTD_subprof=[None]*n_subprof # List of CTD objects
            for kprof in range(n_subprof):
                indprof=np.unique(df_KW["Profile"].values)[kprof]
                CTD_prof=ctd(printlog=show_output)
                CTD_prof.general_attributes["source"]="KivuWatt profiles"
                if indprof in indprof_mSmm:
                    fcond=10
                else:
                    fcond=1
                    
                if indprof in indprof_noconv_depth:
                    fdepth=np.nan
                else:
                    fdepth=0.978
                
                # Read data
                if not CTD_prof.split_profiles_Kivuwatt(df_KW,CTD_metaKW,indprof,multip_cond=fcond,press_to_depth_factor=fdepth):
                    print('Not possible to process profile {}'.format(indprof))
                    continue
                CTD_prof.extract_water_level(lake_level, lake_info["alt"])
                CTD_prof.quality_assurance(directories["quality_assurance_KW"])
                CTD_subprof[kprof]=CTD_prof
        except Exception:
            failed.append(file)
        CTD_subprof=list(np.array(CTD_subprof)[np.array(CTD_subprof)!=None]) # Keep only the profiles that are not empty
    else: # REMA profiles
        # Create CTD object:
        CTD_initial = ctd(printlog=show_output)
        CTD_initial.general_attributes["source"]="Lake Kivu Monitoring Program"

        # Read data:
        if CTD_initial.read_raw_data(os.path.join(directories["Level0_dir"], file), max_date=datetime(2022, 11, 18)):
            CTD_initial.extract_water_level(lake_level, lake_info["alt"]) # Extract water level data
            CTD_initial.extract_meta_data(os.path.join(directories["Level0_dir"], file)) # Extract metadata
            
            # Divide profiles if several profiles present in the file:
            if file in files_severalprof:
                indfile=files_severalprof.index(file)
                n_subprof=len(indstart[indfile]) # Number of subprofiles
                CTD_subprof=[None]*n_subprof # List of CTD objects
                for kprof in np.arange(n_subprof): # Process each subprofile
                    # Copy the CTD data specific to the subprofile:
                    CTD_copy=copy.deepcopy(CTD_initial)
                    for key, values in CTD_copy.data.items():
                        CTD_copy.data[key]=values[indstart[indfile][kprof]:indend[indfile][kprof]]
                    CTD_subprof[kprof]=CTD_copy
            else:
                CTD_subprof=[CTD_initial]
                # Remove data points if specified:
                if file in files_datarem:
                    indrem_file=indrem[files_datarem.index(file)]
                    for var_name in CTD_initial.variables:
                        CTD_initial.data[var_name]=np.delete(CTD_initial.data[var_name],indrem_file)
            
            for CTD in CTD_subprof:
                # Extract the profiling part of the data and process it:
                if CTD.extract_profile():
                    CTD.quality_assurance(directories["quality_assurance"])
                else:
                    failed.append(file)
                    break
        else:
            failed.append(file)
    if file in failed:
        continue # Go to the next file
    
    # Loop on each profile from REMA or Kivuwatt:
    count_subprof=0
    for CTD in CTD_subprof:
        count_subprof+=1
        print('**** Profile {}/{} ****'.format(count_subprof,len(CTD_subprof)))                 
        if CTD.derive_variables(lake_info["lat"],lake_info["alt"],df_gas): # Calculation of additional variables       
            if data_type[index_file]==0: # REMA
                CTD.quality_assurance(directories["quality_assurance"]) # Re-apply quality assurance on newly created variables
                CTD.to_netcdf(directories["Level2A_dir"], "L2A")
                if save_csv:
                    CTD.to_csv(directories["Level2A_dir"], "L2A",dimrows='time')
            else: # Kivuwatt
                CTD.quality_assurance(directories["quality_assurance_KW"])
                CTD.to_netcdf(directories["Level2A_KW_dir"], "L2A")
                if save_csv:
                    CTD.to_csv(directories["Level2A_KW_dir"], "L2A",dimrows='time')
            CTD.mask_data() # Apply the mask from quality check
            # Add latitude and longitude as variables
            CTD.grid["latitude"]=CTD.general_attributes["latitude"]
            CTD.grid["longitude"]=CTD.general_attributes["longitude"]
            CTD.grid["dist_GEF"]=CTD.general_attributes["distance_to_GEF"]
            CTD.profile_to_timeseries_grid(vars_nointerp=["latitude","longitude","dist_GEF"],depthgrid=CTD.data["depth_ref"]) # Don't interpolate latitude and longitude
            if data_type[index_file]==0: # REMA
                CTD.to_netcdf(directories["Level2B_dir"], "L2B", output_period="profile", grid=True)
                if save_csv:
                    CTD.to_csv(directories["Level2B_dir"], "L2B",dimrows='depth_interp',grid=True)
                CTD.to_netcdf_combine(directories["Level3_dir"], "L3_REMA")
            else: # Kivuwatt
                CTD.to_netcdf(directories["Level2B_KW_dir"], "L2B", output_period="profile", grid=True)
                if save_csv:
                    CTD.to_csv(directories["Level2B_KW_dir"], "L2B",dimrows='depth_interp',grid=True)
                CTD.to_netcdf_combine(directories["Level3_dir"], "L3_KW")
        else:
            failed.append(file)

print(failed)

