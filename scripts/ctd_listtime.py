# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 16:35:54 2023

@author: dodatomy
"""

import os
import yaml
from ctd import ctd
from datetime import datetime
import numpy as np
import copy
import pandas as pd

with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

for directory in directories.values():
    if not os.path.exists(directory):
        os.makedirs(directory)

files = os.listdir(directories["Level0_dir"])
files.sort()

failed = []

index_file=0

list_filenames=[]
list_dates=[]

for file in files:
    index_file=index_file+1
    print('********************************')
    print('File '+str(index_file)+'/'+str(len(files))+' ('+str(round(index_file/len(files)*100))+ '%)')
    CTD = ctd()
    if CTD.read_raw_data(os.path.join(directories["Level0_dir"], file), max_date=datetime(2022, 11, 18)):
        list_filenames.append(file)
        list_dates.append(datetime.utcfromtimestamp(CTD.data['time'][0]))
    else:
        failed.append(file)

print(failed)

df=pd.DataFrame({"Filename":list_filenames,"Dates":list_dates})
df.index.name = 'Index_Profiles'
df.to_csv('list_dates_files.csv', sep=",")

