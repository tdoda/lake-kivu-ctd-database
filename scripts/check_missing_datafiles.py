# -*- coding: utf-8 -*-
import os
import yaml
from ctd import ctd
from datetime import datetime, timezone
import numpy as np
import copy
import time
import pandas as pd
import xarray as xr

#%% Parameters
metadatafile="../data/meta_data/0_CTD information_2008-2022_ms_221201.xlsx"


with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)
    
files=[f for f in os.listdir(directories["Level0_dir"]) if f.endswith((".TOB",".cnv")) ]



#%% Open metadata
metadata_dict=pd.read_excel(metadatafile,sheet_name=None)
sheetnames=list(metadata_dict.keys())
datafiles_from_meta=[]
dates_from_meta=[]

for k in range(1,len(sheetnames)):
    datafiles_from_meta.extend(list(metadata_dict[sheetnames[k]]["TOB name in Database"]))
    dates_from_meta.extend(list(metadata_dict[sheetnames[k]]["date"]))
datafiles_from_meta=np.array(datafiles_from_meta)
keep_files=datafiles_from_meta!='nan'
datafiles_from_meta=datafiles_from_meta[keep_files]
dates_from_meta=np.array(dates_from_meta)[keep_files]

#%% Check which data files specified in metadata are missing
ind_missing=[]
missing_files=[]
for k in range(len(datafiles_from_meta)):
    if datafiles_from_meta[k] not in files:
        missing_files.append(datafiles_from_meta[k])
        ind_missing.append(k)

dates_missing=dates_from_meta[ind_missing]

#%% Check which data files from Level0 folder are missing in the metadata
missing_metadata=[]
for k in range(len(files)):
    if files[k] not in datafiles_from_meta:
        missing_metadata.append(files[k])
        
        
#%% Get all data files exported to Level2A
files_L2A=[f for f in os.listdir(directories["Level2A_dir"])]
filenames_L2A=[]

for k in range(len(files_L2A)):
    print(k/len(files_L2A)*100)
    data_L2A=xr.open_dataset(directories["Level2A_dir"]+files_L2A[k])
    filenames_L2A.append(data_L2A.attrs["file_name"])
    data_L2A.close()
    
