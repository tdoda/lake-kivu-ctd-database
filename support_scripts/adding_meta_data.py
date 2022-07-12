# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:00:10 2022

@author: thomitob
"""

import os
import pandas as pd

directory = "../data/Level0/"
df = pd.read_csv('../data/meta_data/All_CTD_Meta_data.csv', delimiter=';')

no_files = len(os.listdir(directory))
meta_files = 0
lost_files = 0
added = 0

for index, row in df.iterrows():
    path = os.path.join(directory, str(row['TOB_name_in_Database:']))
    if os.path.isfile(path):
        meta_files += 1
        df2_series = row.squeeze()
        quote = str(df2_series.to_string())
        with open(path, "r", encoding="utf8", errors='ignore') as f:
            lines = f.readlines()
        if lines[0] != "*** Meta Data ***\n":
            added += 1
            with open(path, "w", encoding="utf8", errors='ignore') as f:
                f.write("*** Meta Data ***")
                f.write("\n")
                f.write(quote)
                f.write("\n")
                f.write("\n")
                f.write("*************")
                f.write("\n")
                f.writelines(lines)
    else:
        lost_files += 1

print("Metadata added for {} files and exists for {} out of {} files.".format(added, meta_files, no_files))
print("{} files have metadata but cannot be located.".format(lost_files))
print("No metadata is available for {} files.".format(no_files-meta_files))



