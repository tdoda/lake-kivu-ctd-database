# -*- coding: utf-8 -*-
import os
import yaml
from ctd import ctd
from datetime import datetime, timezone
import numpy as np
import copy
import pandas as pd
import time

lake_info = {"lat": -2, "alt": 1462}
lake_level = "../data/lake_level/c_gls.json"

with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

for directory in directories.values():
    if not os.path.exists(directory):
        os.makedirs(directory)

files=[f for f in os.listdir(directories["Level0_KW_dir"]) if f.endswith((".csv")) ]

files.sort()
failed = []


# Period to remove:
dateperiod_rem=[] # Time limits of the period
tperiod_rem=[dateperiod_rem[k].replace(tzinfo=timezone.utc).timestamp() for k in np.arange(len(dateperiod_rem))]

# Profiles with conductivity in mS/mm (first profile: kprof=1):
indprof_mSmm=np.arange(23,30,1)
index_file=0

CTD_meta = ctd()
CTD_meta.extract_meta_data_Kivuwatt(os.path.join(directories["Level0_KW_dir"], 'Metadata.csv'))

# Read the data
count=0
print('********************************')
print("Reading data...")

for file in files:
    index_file=index_file+1
    print('File '+str(index_file)+'/'+str(len(files))+' ('+str(round(index_file/len(files)*100))+ '%)')
    if 'Data' in file:
        try:
            df=pd.read_csv(os.path.join(directories["Level0_KW_dir"], file),encoding='ISO-8859-1',sep=',',
                            header=0,names=['Profile','Hour','Press','Depth_KW','Temp','Cond'],dtype={'Time':str})
            if count==0:
                df_allCTD=df
            else:
                df_allCTD=pd.concat([df_allCTD,df]) 
            count=count+1
        except Exception:
            failed.append(file)
            
print(failed)
failed_prof=[]

# Split the data in different profiles
start_time=time.time()
#for kprof in np.unique(df_allCTD["Profile"].values):
for kprof in np.arange(30,88,1):
    print('********************************')
    # if kprof==11:
    #     end_time=time.time()
    #     time_prof=end_time-start_time
    # if kprof>=11:
    #     time_rem=(len(np.unique(df_allCTD["Profile"].values))-kprof)*time_prof/600
    #     print('Profile {}/{} ({}%). Time remaining: {:.1f} min'.format(kprof,len(np.unique(df_allCTD["Profile"].values)),round(kprof/len(np.unique(df_allCTD["Profile"].values))*100),time_rem))
    # else:
        # print('Profile {}/{} ({}%)'.format(kprof,len(np.unique(df_allCTD["Profile"].values)),round(kprof/len(np.unique(df_allCTD["Profile"].values))*100)))
    CTD=ctd()
    try:
        if kprof in indprof_mSmm:
            if not CTD.split_profiles_Kivuwatt(df_allCTD,CTD_meta,kprof,multip_cond=10):
                raise Exception('Not possible to process profile')
        else:
            if not CTD.split_profiles_Kivuwatt(df_allCTD,CTD_meta,kprof,multip_cond=1):
                raise Exception('Not possible to process profile')
        print('Done')
        CTD.extract_water_level(lake_level, lake_info["alt"])
        #CTD.extract_profile() 
        CTD.air_press=np.nan # Unkown air pressure
        
        CTD.quality_assurance(directories["quality_assurance_KW"])
        if CTD.derive_variables(lake_info["lat"], lake_info["alt"],estimated_depth=list(CTD.data["Depth_KW"])):
            CTD.quality_assurance(directories["quality_assurance_KW"]) # Re-apply quality assurance on newly created variables
            CTD.to_netcdf(directories["Level2A_KW_dir"], "L2A")
            CTD.mask_data() # Apply the mask from quality check
            # Add latitude and longitude as variables
            CTD.grid["latitude"]=CTD.general_attributes["latitude"]
            CTD.grid["longitude"]=CTD.general_attributes["longitude"]
            CTD.grid["dist_GEF"]=CTD.general_attributes["distance_to_GEF"]
            CTD.profile_to_timeseries_grid(vars_nointerp=["latitude","longitude","dist_GEF"],depthgrid=CTD.data["Depth_KW"]) # Don't interpolate latitude and longitude
            CTD.to_netcdf(directories["Level2B_KW_dir"], "L2B", output_period="monthly", grid=True)
    except Exception:
        breakpoint()
        failed_prof.append(kprof)

print('Profiles with errors:')
print(failed_prof)



