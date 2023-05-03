# -*- coding: utf-8 -*-
import os
import yaml
from ctd import ctd
from datetime import datetime, timezone
import numpy as np
import copy
import time

lake_info = {"lat": -2, "alt": 1462}
lake_level = "../data/lake_level/c_gls.json"

with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

for directory in directories.values():
    if not os.path.exists(directory):
        os.makedirs(directory)


files=[f for f in os.listdir(directories["Level0_dir"]) if f.endswith((".TOB",".cnv")) ]
# files_SBE=[]
# for k in np.arange(len(files)):
#     if files[k].endswith(".cnv"):
#         files_SBE.append(files[k])
# files=files_SBE

files.sort()
failed = []

# Files with several profiles:
files_severalprof=['SA241437_6.TOB','SA241437_8.TOB']
indstart=[[1004,3719,10031],[1096,6352,12450]]
indend=[[3718,9165,14210],[5090,10250,15603]]
index_file=0

# Files with data to remove
files_datarem=['SBE19plus_01907894_2020_11_02_0002.cnv']
indrem=[[15194]]

start_time=time.time()
for file in files:
    index_file=index_file+1
    print('********************************')
    
    if index_file==11:
        end_time=time.time()
        time_prof=end_time-start_time
    if index_file>=11:
        time_rem=(len(files)-index_file)*time_prof/600
        print('File {}/{} ({}%). Time remaining: {:.1f} min'.format(index_file,len(files),round(index_file/len(files)*100),time_rem))
    else:
        print('File {}/{} ({}%)'.format(index_file,len(files),round(index_file/len(files)*100)))
    
    
    
    CTD = ctd()
    CTD.general_attributes["source"]="Lake Kivu Monitoring Program"
    
    if CTD.read_raw_data(os.path.join(directories["Level0_dir"], file), max_date=datetime(2022, 11, 18)):
        CTD.extract_water_level(lake_level, lake_info["alt"])
        CTD.extract_meta_data(os.path.join(directories["Level0_dir"], file))
        # Cut profiles if necessary
        if file in files_severalprof:
            indfile=files_severalprof.index(file)
            for kprof in np.arange(0,len(indstart)+1,1):
                CTD_copy=copy.deepcopy(CTD)
                keep_period=1
                for key, values in CTD_copy.data.items():
                    CTD_copy.data[key]=values[indstart[indfile][kprof]:indend[indfile][kprof]]
                if CTD_copy.extract_profile():
                    CTD_copy.quality_assurance(directories["quality_assurance"])
                    if CTD_copy.derive_variables(lake_info["lat"], lake_info["alt"]):
                        CTD_copy.quality_assurance(directories["quality_assurance"])
                        CTD_copy.to_netcdf(directories["Level2A_dir"], "L2A")
                        CTD_copy.mask_data() # Apply the mask from quality check
                        # Add latitude and longitude as variables
                        CTD_copy.grid["latitude"]=CTD_copy.general_attributes["latitude"]
                        CTD_copy.grid["longitude"]=CTD_copy.general_attributes["longitude"]
                        CTD_copy.grid["dist_GEF"]=CTD_copy.general_attributes["distance_to_GEF"]
                        CTD_copy.profile_to_timeseries_grid(vars_nointerp=["latitude","longitude","dist_GEF"]) # Don't interpolate latitude and longitude
                        CTD_copy.to_netcdf(directories["Level2B_dir"], "L2B", output_period="monthly", grid=True)
                else:
                    failed.append(file)   
        else:
            keep_period=1
            if file in files_datarem:
                indrem_file=indrem[files_datarem.index(file)]
                for var_name in CTD.variables:
                    CTD.data[var_name]=np.delete(CTD.data[var_name],indrem_file)
            if CTD.extract_profile():
                CTD.quality_assurance(directories["quality_assurance"])
                if CTD.derive_variables(lake_info["lat"], lake_info["alt"]):
                    CTD.quality_assurance(directories["quality_assurance"]) # Re-apply quality assurance on newly created variables
                    CTD.to_netcdf(directories["Level2A_dir"], "L2A")
                    CTD.mask_data() # Apply the mask from quality check
                    # Add latitude and longitude as variables
                    CTD.grid["latitude"]=CTD.general_attributes["latitude"]
                    CTD.grid["longitude"]=CTD.general_attributes["longitude"]
                    CTD.grid["dist_GEF"]=CTD.general_attributes["distance_to_GEF"]
                    CTD.profile_to_timeseries_grid(vars_nointerp=["latitude","longitude","dist_GEF"],depthgrid=CTD.data["depth_ref"]) # Don't interpolate latitude and longitude
                    CTD.to_netcdf(directories["Level2B_dir"], "L2B", output_period="monthly", grid=True)
            else:
                failed.append(file)
    else:
        failed.append(file)

print(failed)

