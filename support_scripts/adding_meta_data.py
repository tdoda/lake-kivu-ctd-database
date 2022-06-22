# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:00:10 2022

@author: thomitob
"""

import os
import pandas as pd


directory = "../data/level0"
df = pd.read_csv('../data/meta_data/All_CTD_Meta_data.csv', delimiter=';')

for filename in os.listdir(directory):
    try:
        df2 = df.loc[df['TOB_name_in_Database:'] == filename].iloc[0]
        df2_series = df2.squeeze()
        quote = str(df2_series.to_string())
        f1 = os.path.join(directory, filename)
        if os.path.isfile(f1):
            print(filename)
            with open(f1, "r+") as f:
                first_line = f.readline()
                print(first_line)
                if first_line != "*** Meta Data ***\n": 
                    lines = f.readlines()
                    f.seek(0)
                    f.write("*** Meta Data ***")
                    f.write("\n")
                    f.write(quote)
                    f.write("\n")
                    f.write("\n")
                    f.write("*************")
                    f.write("\n")
                    f.write(first_line)
                    f.writelines(lines) 
    except:
        print(filename, "no meta data")
              

