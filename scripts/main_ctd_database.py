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
import sys
import netCDF4
import yaml
from ctd import ctd
from datetime import datetime, timezone, UTC
import numpy as np
import copy
import time
import pandas as pd
from functions import *

# Make sure the current working directory is the one of the script (to avoid problems with relative paths):
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#%% Choices for the database creation
show_output=False # To print the different steps in the console with the log function
save_csv=True # To save the data of L2A and L2B as csv files in addition to netCDF files


#%% Parameters
lake_info = {"lat": -2, "alt": 1462} # Latitude [°] and altitude [m]
lake_level = "../data/lake_level/c_gls.json" # File containing the lake level data
min_date_period=datetime(2001, 1, 1) # Minimum date of the profiles to include in the database

# Import the name of directories:
with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader) 

# Create the directories if not existing:
for directory in directories.values(): 
    if not os.path.exists(directory):
        os.makedirs(directory)

# List of datafiles to read (could specify a specific file name here):
# files_REMA=[]
files_KW=[]

# To reprocess all files:
files_REMA=[f for f in os.listdir(directories["Level0_dir"]) if f.endswith((".TOB",".cnv")) ]
# files_KW=[f for f in os.listdir(directories["Level0_KW_dir"]) if f.endswith((".csv")) and f.startswith('D')]


# Associate the data type to each file (REMA or Kivuwatt)
files_REMA.sort()
files_KW.sort()
files=files_REMA+files_KW
data_type=[0]*len(files_REMA)+[1]*len(files_KW) # Data type = 0 for REMA and = 1 for KW
data_type_name=["REMA","Kivuwatt"]
failed = []
files_L2B_REMA=[]
files_L2B_KW=[]

#%% Manual corrections

# Files with several profiles (to divide manually):
files_severalprof=['SA241437_6.TOB','SA241437_8.TOB']
indstart=[[1004,3719,10031],[1096,6352,12450]]
indend=[[3718,9165,14210],[5090,10250,15603]]


# Files with data to remove manually:
files_datarem=['SBE19plus_01907894_2020_11_02_0002.cnv']
indrem=[[15194]]

# Periods to remove for the combined database only
# Periods to remove (government):
dateperiod_rem=[[datetime(2016,1,14,11,0,0),datetime(2016,1,14,12,0,0)],[datetime(2016,2,10,11,0,0),datetime(2016,2,10,14,0,0)],\
                [datetime(2019,9,3,0,0,0),datetime(2019,9,4,0,0)],[datetime(2019,10,28),datetime(2019,10,29)],\
                    [datetime(2020,3,17),datetime(2020,3,18)],[datetime(2021,6,3,10,40,0),datetime(2021,6,3,11,0,0)]] # Time limits of the period (density peak, wrong pressue calibration (?), wrong conductivity/temperature)
tperiod_rem=[None]*len(dateperiod_rem)
for kperiod in np.arange(len(dateperiod_rem)):
    tperiod_rem[kperiod]=[dateperiod_rem[kperiod][k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    
 # Periods to remove (Kivuwatt):   
dateperiod_rem_KW=[[datetime(2019,11,7,9,0,0),datetime(2019,11,7,10,0,0)],[datetime(2021,6,3),datetime(2021,6,11)]] # Time limits of the period (depth shift, different depth calculation)
tperiod_rem_KW=[None]*len(dateperiod_rem_KW)
for kperiod in np.arange(len(dateperiod_rem_KW)):
    tperiod_rem_KW[kperiod]=[dateperiod_rem_KW[kperiod][k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    
    
tperiod_rem_all=[tperiod_rem,tperiod_rem_KW]

# Kivuwatt profiles with conductivity in mS/mm (profile indices corresponds to the first column of the datafile):
indprof_mSmm=np.arange(23,30,1)

# Profiles with different conversion pressure-depth (profile indices corresponds to the first column of the datafile):
indprof_noconv_depth=np.arange(562,572,1)

# Metadata for Kivuwatt profiles:
CTD_metaKW = ctd(printlog=show_output)
CTD_metaKW.extract_meta_data_Kivuwatt(os.path.join(directories["Level0_KW_dir"], 'Metadata.csv'))

# Load gas data
df_gas=pd.read_excel('../data/gas_profile/Gas_profile.xlsx',names=['Depth','CH4','CH4_err','CO2','CO2_err'])

# Create txt file to save name of data files not included in database
with open("../data/ctd/files_removed.txt", "a") as file_txt:
    file_txt.write("*****************\nFiles not included in database ({})\n*****************\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
#breakpoint()
#%% Data extraction and export to Levels 2A and 2B

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
        print('File {}/{} ({}%): {}, {}. Time remaining: {:.1f} min'.format(index_file+1,len(files),round((index_file+1)/len(files)*100),file,data_type_name[data_type[index_file]],time_rem))
    else:
        print('File {}/{} ({}%): {}, {}'.format(index_file+1,len(files),round((index_file+1)/len(files)*100),file,data_type_name[data_type[index_file]]))
        
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
                CTD_prof.general_attributes["filename"]=file
                if indprof in indprof_mSmm:
                    fcond=10
                else:
                    fcond=1
                    
                if indprof in indprof_noconv_depth:
                    # fdepth=np.nan
                    # Skip file:
                    continue
                else:
                    fdepth=0.978
                    
                
                # Read data
                if not CTD_prof.split_profiles_Kivuwatt(df_KW,CTD_metaKW,indprof,multip_cond=fcond,press_to_depth_factor=fdepth):
                    print('Not possible to process profile {}'.format(indprof))
                    with open("../data/ctd/files_removed.txt", "a") as file_txt:
                        file_txt.write(file+": profile {}/{} could not be processed (function split_profiles_Kivuwatt)\n".format(indprof,n_subprof))
                    continue
                CTD_prof.extract_water_level(lake_level, lake_info["alt"])
                CTD_prof.quality_assurance(directories["quality_assurance_KW"])
                CTD_subprof[kprof]=CTD_prof
        except Exception:
            failed.append(file)
            with open("../data/ctd/files_removed.txt", "a") as file_txt:
                file_txt.write(file+": Kivuwatt profile could not be extracted\n")
            print('Kivuwatt profile data could not be read')
        CTD_subprof=list(np.array(CTD_subprof)[np.array(CTD_subprof)!=None]) # Keep only the profiles that are not empty
    else: # REMA profiles
        # Create CTD object:
        CTD_initial = ctd(printlog=show_output)
        CTD_initial.general_attributes["source"]="Lake Kivu Monitoring Program"
        CTD_initial.general_attributes["filename"]=file

        # Read data:
        if CTD_initial.read_raw_data(os.path.join(directories["Level0_dir"], file), max_date=datetime(2022, 11, 18),min_date=min_date_period):
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
            ksubprof=0
            for CTD in CTD_subprof:
                ksubprof+=1
                # Extract the profiling part of the data and process it:
                if CTD.extract_profile():
                    CTD.quality_assurance(directories["quality_assurance"])
                else:
                    failed.append(file)
                    with open("../data/ctd/files_removed.txt", "a") as file:
                        file.write(file+": profile {}/{} could not be extracted\n".format(ksubprof,len(CTD_subprof)))
                    break
        else:
            failed.append(file)
            with open("../data/ctd/files_removed.txt", "a") as file_txt:
                file_txt.write(file+": file could not be read (function read_raw_data)\n")
            
            
        if file in failed:
            print('Profile data in {} could not be read, see data/ctd/files_removed.txt for more information'.format(file))
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
                    CTD.to_csv(directories["Level2A_dir"], "L2A",dimrows='time',var_to_remove=["thorpe","pt","prho"])
            else: # Kivuwatt
                CTD.quality_assurance(directories["quality_assurance_KW"])
                CTD.to_netcdf(directories["Level2A_KW_dir"], "L2A")
                if save_csv:
                    CTD.to_csv(directories["Level2A_KW_dir"], "L2A",dimrows='time',var_to_remove=["thorpe","pt","prho"])
            CTD.mask_data() # Apply the mask from quality check
            # Add latitude and longitude as variables
            CTD.grid["latitude"]=CTD.general_attributes["latitude"]
            CTD.grid["longitude"]=CTD.general_attributes["longitude"]
            CTD.grid["dist_GEF"]=CTD.general_attributes["distance_to_GEF"]
            CTD.profile_to_timeseries_grid(vars_nointerp=["latitude","longitude","dist_GEF"],depthgrid=CTD.data["depth_ref"]) # Don't interpolate latitude and longitude
            if data_type[index_file]==0: # REMA
                CTD.to_netcdf(directories["Level2B_dir"], "L2B", output_period="profile", grid=True)
                files_L2B_REMA.append(CTD.L2B_filename)
                if save_csv:
                    CTD.to_csv(directories["Level2B_dir"], "L2B",dimrows='depth_interp',grid=True)
                # CTD.to_netcdf_combine(directories["Level3_dir"], "L3_REMA")
            else: # Kivuwatt
                CTD.to_netcdf(directories["Level2B_KW_dir"], "L2B", output_period="profile", grid=True)
                files_L2B_KW.append(CTD.L2B_filename)
                if save_csv:
                    CTD.to_csv(directories["Level2B_KW_dir"], "L2B",dimrows='depth_interp',grid=True)
                # CTD.to_netcdf_combine(directories["Level3_dir"], "L3_KW")
        else:
            failed.append(CTD.general_attributes["filename"])
            with open("../data/ctd/files_removed.txt", "a") as file_txt:
                file_txt.write(CTD.general_attributes["filename"]+": additional variables could be calculated\n")
            

print('Files not processed:')
print(failed)


#%% Combine all the L2B profiles from the selected files above and export them to Level 3
#breakpoint()

start_time=time.time() # current time
index_file=-1

# Get data from existing L3 files
folder_REMA=directories["Level3_dir"]+"REMA/"
folder_KW=directories["Level3_dir"]+"Kivuwatt/"
folder_comb=directories["Level3_dir"]+"Combined/"
if not os.path.exists(folder_REMA): # Create folder if it doesn't exist
    os.makedirs(folder_REMA)
if not os.path.exists(folder_KW): # Create folder if it doesn't exist
    os.makedirs(folder_KW)
if not os.path.exists(folder_comb): # Create folder if it doesn't exist
    os.makedirs(folder_comb)


L3_REMA = os.path.join(folder_REMA, "L3_REMA.nc")
L3_KW = os.path.join(folder_KW, "L3_KW.nc")
L3_comb = os.path.join(folder_comb, "L3_comb.nc")

if os.path.isfile(L3_REMA): # File has already been created
    nc_REMA = netCDF4.Dataset(L3_REMA, mode='a', format='NETCDF4')
    try: 
        nc_REMA__time = nc_REMA.variables["time"]
        data_nc_REMA=get_nc_data(nc_REMA) 
        createL3_REMA=False
    except:
        createL3_REMA=True
        data_nc_REMA=dict()
    nc_REMA.close()
else:
    files_L2B_REMA=[f for f in os.listdir(directories["Level2B_dir"]) if f.endswith((".nc")) ]# Get all the L2B files
    data_nc_REMA=dict()
    createL3_REMA=True
    
if os.path.isfile(L3_KW): # File has already been created
    nc_KW = netCDF4.Dataset(L3_KW, mode='a', format='NETCDF4')
    try:
        nc_KW__time = nc_KW.variables["time"]
        data_nc_KW=get_nc_data(nc_KW) 
        createL3_KW=False
    except:
        createL3_KW=True
        data_nc_KW=dict()
    nc_KW.close()
else:
    files_L2B_KW=[f for f in os.listdir(directories["Level2B_KW_dir"]) if f.endswith((".nc")) ] # Get all the L2B files
    data_nc_KW=dict()
    createL3_KW=True
    




print('********************************')
print('Combine all the profiles')
print('')

files_remove=[]

# To reprocess all the files
# files_L2B_REMA=[f for f in os.listdir(directories["Level2B_dir"]) if f.endswith((".nc")) ]
# files_L2B_KW=[f for f in os.listdir(directories["Level2B_KW_dir"]) if f.endswith((".nc")) ]
files_L2B=files_L2B_REMA+files_L2B_KW
if len(files_L2B)==0: # No file to process
    print('No file to process!')
    sys.exit()
    
data_type_L2B=[0]*len(files_L2B_REMA)+[1]*len(files_L2B_KW)

for file in files_L2B:
    index_file=index_file+1
    
    # Display progress
    if index_file==20:
        end_time=time.time()
        time_prof=(end_time-start_time)/20 # time needed to process one profile [s]
    if index_file>=20:
        time_rem=(len(files_L2B)-index_file-1)*time_prof/60 # Remaining time [min]
        print('File {}/{} ({}%): {}. Time remaining: {:.1f} min'.format(index_file+1,len(files_L2B),round((index_file+1)/len(files_L2B)*100),data_type_name[data_type_L2B[index_file]],time_rem))
    else:
        print('File {}/{} ({}%): {}'.format(index_file+1,len(files_L2B),round((index_file+1)/len(files_L2B)*100),data_type_name[data_type_L2B[index_file]]))
    
    
    # Open L2B file
    if data_type_L2B[index_file]==0: # REMA
        nc_L2B=netCDF4.Dataset(os.path.join(directories["Level2B_dir"],file), mode='a', format='NETCDF4')
        tprof=nc_L2B.variables["time"][:].data[0]
        if np.sum(np.logical_and(tprof>np.array(tperiod_rem_all[0])[:,0],tprof<np.array(tperiod_rem_all[0])[:,1]))>0: # Profile was taken during the period to remove
            files_remove.append(file)  
            with open("../data/ctd/files_removed.txt", "a") as file_txt:
                file_txt.write(file+": not included in L3 file because it belongs to a period with incorrect data\n")
            
            continue
    else: # Kivuwatt
        nc_L2B=netCDF4.Dataset(os.path.join(directories["Level2B_KW_dir"],file), mode='a', format='NETCDF4')
        tprof=nc_L2B.variables["time"][:].data[0]
        if np.sum(np.logical_and(tprof>np.array(tperiod_rem_all[1])[:,0],tprof<np.array(tperiod_rem_all[1])[:,1]))>0: # Profile was taken during the period to remove
            files_remove.append(file) 
            with open("../data/ctd/files_removed.txt", "a") as file_txt:
                file_txt.write(file+": not included in L3 file because it belongs to a period with incorrect data\n")
            continue
    
   
    # Copy the data in CTD object
    CTD_L2B=ctd(printlog=show_output)
    remvar=[]
    for key, values in CTD_L2B.comb_variables.items():
        if key in list(nc_L2B.variables):
            CTD_L2B.grid[key]=nc_L2B.variables[key][:].data
        else: # Delete the variable from the CTD object (won't be exported to netCDF)
            remvar.append(key)
            
    # Delete variables from the CTD object
    for key in remvar:
        del CTD_L2B.comb_variables[key]
    
    # Add the data to the dictionary
    if data_type_L2B[index_file]==0: # REMA
        # CTD_L2B.write_to_L3(nc_REMA,newfile=createL3_REMA)
        CTD_L2B.add_to_dict(data_nc_REMA,newfile=createL3_REMA)
        if createL3_REMA:
            createL3_REMA=False
    else: # Kivuwatt
        # CTD_L2B.write_to_L3(nc_KW,newfile=createL3_KW)
        CTD_L2B.add_to_dict(data_nc_KW,newfile=createL3_KW)
        if createL3_KW:
            createL3_KW=False
    nc_L2B.close()

print('Files removed:')
print(files_remove)
    
# Add datetime, min depth and max depth to the dictionaries:
if data_nc_REMA: # If not empty
    data_nc_REMA["datetime"]=np.array([int(datetime.fromtimestamp(data_nc_REMA["time"][i],UTC).strftime('%Y%m%d%H%M%S')) for i in range(len(data_nc_REMA["time"]))])   
    data_nc_REMA["min_depth"]=np.array([data_nc_REMA["depth_interp"][np.where(~np.isnan(data_nc_REMA["rho"][:,i]))[0][0]] for i in range(len(data_nc_REMA["time"]))])
    data_nc_REMA["max_depth"]=np.array([data_nc_REMA["depth_interp"][np.where(~np.isnan(data_nc_REMA["rho"][:,i]))[0][-1]] for i in range(len(data_nc_REMA["time"]))])
if data_nc_KW: # If not empty
    data_nc_KW["datetime"]=np.array([int(datetime.fromtimestamp(data_nc_KW["time"][i],UTC).strftime('%Y%m%d%H%M%S'))for i in range(len(data_nc_KW["time"]))]) 
    data_nc_KW["min_depth"]=np.array([data_nc_KW["depth_interp"][np.where(~np.isnan(data_nc_KW["rho"][:,i]))[0][0]] for i in range(len(data_nc_KW["time"]))])
    data_nc_KW["max_depth"]=np.array([data_nc_KW["depth_interp"][np.where(~np.isnan(data_nc_KW["rho"][:,i]))[0][-1]] for i in range(len(data_nc_KW["time"]))])

    
# Export the combined profiles to netCDF file (overwrite)
nc_REMA = netCDF4.Dataset(L3_REMA, mode='w', format='NETCDF4')
nc_KW = netCDF4.Dataset(L3_KW, mode='w', format='NETCDF4')
nc_comb = netCDF4.Dataset(L3_comb, mode='w', format='NETCDF4')

# Copy the data in CTD objects and export it to netCDF files
# A. REMA
CTD_REMA=ctd(printlog=show_output)
CTD_REMA.general_attributes["source"]="Lake Kivu Monitoring Program"
if data_nc_REMA: # Not empty
    remvar=[]
    for key, values in CTD_REMA.comb_variables.items():
        if key in data_nc_REMA.keys():
            CTD_REMA.grid[key]=data_nc_REMA[key]
    else: # Delete the variable from the CTD object (won't be exported to netCDF)
        remvar.append(key)
    for key in remvar:
        del CTD_REMA.comb_variables[key]
    CTD_REMA.write_to_L3(nc_REMA,newfile=True)
    CTD_REMA.var_to_csv(folder_REMA, "L3_REMA", ["Temp","rho","SALIN","Cond20"])

# B. Kivuwatt
CTD_KW=ctd(printlog=show_output)
CTD_KW.general_attributes["source"]="Kivuwatt profiles"
if data_nc_KW: # Not empty
    remvar=[]
    for key, values in CTD_KW.comb_variables.items():
        if key in data_nc_KW.keys():
            CTD_KW.grid[key]=data_nc_KW[key]
        else: # Delete the variable from the CTD object (won't be exported to netCDF)
            remvar.append(key)
    for key in remvar:
        del CTD_KW.comb_variables[key]
    CTD_KW.write_to_L3(nc_KW,newfile=True)
    CTD_KW.var_to_csv(folder_KW, "L3_KW", ["Temp","rho","SALIN","Cond20"])
    
# C. Combined
CTD_comb=ctd(printlog=show_output)
CTD_comb.general_attributes["source"]="Combined Kivuwatt-REMA profiles"
time_comb=np.concatenate((data_nc_REMA["time"],data_nc_KW["time"]))
indsort=np.argsort(time_comb)
remvar=[]
for key, values in CTD_comb.comb_variables.items():
    if key in data_nc_KW.keys():
        if len(data_nc_REMA[key].shape)==1:
            if len(data_nc_REMA[key])==len(data_nc_REMA["time"]): # Time series format
                data_comb=np.concatenate((data_nc_REMA[key],data_nc_KW[key]))
                CTD_comb.grid[key]=data_comb[indsort]
            else: # Depth format
                CTD_comb.grid[key]=data_nc_REMA[key]
        else:
            data_comb=np.concatenate((data_nc_REMA[key],data_nc_KW[key]),axis=1)
            CTD_comb.grid[key]=data_comb[:,indsort]
    else:
        if key!="data_type":  
            remvar.append(key)
for key in remvar:
    del CTD_comb.comb_variables[key]
CTD_comb.grid["data_type"]=np.array([0]*len(data_nc_REMA["time"])+[1]*len(data_nc_KW["time"]))[indsort]
CTD_comb.write_to_L3(nc_comb,newfile=True)
CTD_comb.var_to_csv(folder_comb, "L3_comb", ["Temp","rho","SALIN","Cond20"])
    
    


nc_REMA.close()
nc_KW.close()
nc_comb.close()

print('Database created!')


