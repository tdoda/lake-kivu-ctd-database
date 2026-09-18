# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:00:10 2022

@author: thomitob
"""

import os
import pandas as pd


# ---------------------------------------------------------
# ADD METADATA ON TOBs: Without interface (uncomment inputs and call the function)
# ---------------------------------------------------------

#directory = "../data/Level0/"
#metadata = '../data/meta_data/0_CTD information_2008-2022_ms_221201.xlsx'
# start_year = 2023
# end_year = 2025

def add_metadata(metadata, directory, start_year, end_year):
    columns = ["Campaign_number:", "Profile_count:", "Profile:", "date:", "Latitude_S_(digital):", "Longitude_E_(digital):",
            "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):", "TOB_name_in_Database:", "Purpose_of_sampling:",
            "pH_Calibration_(7):", "pH_Calibration_(9):", "pH_Calibration_(10):", "pH_Calibration_(4):"]

    no_files = len(os.listdir(directory))
    meta_files = 0
    lost_files = 0
    added = 0

    for year in range(start_year, end_year+1):
        print(year)
        df = pd.read_excel(metadata, sheet_name=str(year), engine='openpyxl', header=None, skiprows=2)
        df = df.iloc[:, :15]
        df.columns = columns
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
                print(path)
                lost_files += 1

    print("Metadata added for {} files and exists for {} out of {} files.".format(added, meta_files, no_files))
    print("{} files have metadata but cannot be located.".format(lost_files))
    print("No metadata is available for {} files.".format(no_files-meta_files))

    return {
    "added_metadata": added,
    "existing_metadata": meta_files,
    "total_tob_files": no_files,
    "lost_files": lost_files,
    "no_metadata_available": no_files - meta_files
    }


# ---------------------------------------------------------
# ADD METADATA ON TOBs: With interface (any change will affect the ../scripts/database_interface.py)
# ---------------------------------------------------------
def add_metadata_GUI(metadata_path, tob_directory, start_year, end_year):
    # Convert to integers exactly like original
    sy = int(start_year)
    ey = int(end_year)

    columns = [
        "Campaign_number:", "Profile_count:", "Profile:", "date:",
        "Latitude_S_(digital):", "Longitude_E_(digital):",
        "Distance_to_GEF_(m):", "Rope_length_(m):", "Max_depth_(m):",
        "TOB_name_in_Database:", "Purpose_of_sampling:",
        "pH_Calibration_(7):", "pH_Calibration_(9):",
        "pH_Calibration_(10):", "pH_Calibration_(4):"
    ]

    meta_files = 0
    lost_files = 0
    added = 0
    total_rows = 0

    # Count rows first (same as original)
    for year in range(sy, ey + 1):
        df = pd.read_excel(metadata_path, sheet_name=str(year),
                           engine='openpyxl', header=None, skiprows=2)
        df = df.iloc[:, :15]
        total_rows += len(df)

    processed_rows = 0

    # Process metadata row-by-row
    for year in range(sy, ey + 1):
        df = pd.read_excel(metadata_path, sheet_name=str(year),
                           engine='openpyxl', header=None, skiprows=2)
        df = df.iloc[:, :15]
        df.columns = columns

        for _, row in df.iterrows():
            path = os.path.join(tob_directory, str(row["TOB_name_in_Database:"]))

            if os.path.isfile(path):
                meta_files += 1
                quote = str(row.squeeze().to_string())

                with open(path, "r", encoding="utf8", errors="ignore") as f:
                    lines = f.readlines()

                # EXACT original behavior preserved
                if lines and lines[0] != "*** Meta Data ***\n":
                    added += 1
                    with open(path, "w", encoding="utf8", errors="ignore") as f:
                        f.write("*** Meta Data ***\n")
                        f.write(quote + "\n\n*************\n")
                        f.writelines(lines)
            else:
                lost_files += 1

            processed_rows += 1

            yield processed_rows, total_rows, meta_files, lost_files, added





