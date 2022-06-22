# -*- coding: utf-8 -*-
import os
import yaml
from ctd import ctd

lake_info = {"lat": -2, "alt": 1462}
lake_level = "../data/lake_level/c_gls.json"

with open("input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

for directory in directories.values():
    if not os.path.exists(directory):
        os.makedirs(directory)

files = os.listdir(directories["Level0_dir"])
files.sort()

for file in files:
    CTD = ctd()
    valid = CTD.read_raw_data(os.path.join(directories["Level0_dir"], file))
    if valid:
        CTD.extract_water_level(lake_level, lake_info["alt"])
        CTD.extract_profile()
        CTD.quality_assurance(directories["quality_assurance"])
        CTD.to_netcdf(directories["Level1_dir"], "L1")
        # if CTD.derive_variables(lake_info["lat"], lake_info["alt"]):
        #     CTD.quality_assurance(directories["quality_assurance"])
        #     CTD.to_netcdf(directories["Level2A_dir"], "L2A")
        #     CTD.mask_data()
        #     CTD.profile_to_timeseries_grid()
        #     CTD.to_netcdf(directories["Level2B_dir"], "L2B", output_period="yearly", grid=True)
