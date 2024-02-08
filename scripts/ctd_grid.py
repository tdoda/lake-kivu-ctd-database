# -*- coding: utf-8 -*-
import os
import sys
import json
import netCDF4
import dateparser
import numpy as np
import pandas as pd
import math
from copy import deepcopy
from envass import qualityassurance
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from scipy import interpolate
import seawater as sw
import re as re
import matplotlib.pyplot as plt
import collections
from functions import *


class ctd_grid:
    def __init__(self):
        self.general_attributes = {
            "institution": "Eawag",
            "references": "james.runnalls@eawag.ch",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "CTD profiles for Lake Kivu ",
            "title": "Lake Kivu CTD",
            "latitude": "-1.850964",
            "longitude": "29.208903",
        }

        self.dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            "depth_interp": {'dim_name': "depth_interp", 'dim_size': None}
        }

        
        self.variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            'datetime': {'var_name': 'datetime', 'dim': ('time',), 'unit': '-', 'longname': 'Date and time as integer yyyymmddHHMMSS'},
            'min_depth': {'var_name': 'min_depth', 'dim': ('time',), 'unit': 'm', 'longname': 'Minimum depth'},
            'max_depth': {'var_name': 'max_depth', 'dim': ('time',), 'unit': 'm', 'longname': 'Maximum depth'},
            'Press': {'var_name':'Press', 'dim':('depth_interp','time'), 'unit': 'dbar', 'longname': 'pressure'},
            "depth_interp": {'var_name': "depth_interp", 'dim': ('depth_interp',), 'unit': 'm', 'longname': "Interpolated depth"},
            'Temp': {'var_name': 'Temp', 'dim': ('depth_interp', 'time'), 'unit': 'degC', 'longname': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('depth_interp', 'time'), 'unit': 'mS/cm', 'longname': 'conductivity'},
            'Chl_A': {'var_name': 'Chl_A', 'dim': ('depth_interp', 'time'), 'unit': 'g/l', 'longname': 'chlorophyll A'},
            'Turb': {'var_name': 'Turb', 'dim': ('depth_interp', 'time'), 'unit': 'FTU', 'longname': 'Turbidity'},
            'pH': {'var_name': 'pH', 'dim': ('depth_interp', 'time'), 'unit': '_', 'longname': 'pH'},
            'sat': {'var_name': 'sat', 'dim': ('depth_interp', 'time'), 'unit': '%', 'longname': 'oxygen saturation'},
            'DO_mg': {'var_name': 'DO_mg', 'dim': ('depth_interp', 'time'), 'unit': 'mg/l', 'longname': 'oxygen concentration'},
            "rho": {'var_name': "rho", 'dim': ('depth_interp', 'time'), 'unit': 'kg/m3', 'longname': "Density", },
            "pt": {'var_name': "pt", 'dim': ('depth_interp', 'time'), 'unit': 'degC', 'longname': "Potential Temperature", },
            "prho": {'var_name': "prho", 'dim': ('depth_interp', 'time'), 'unit': 'kg/m3', 'longname': "Potential Density"},
            "thorpe": {'var_name': "thorpe", 'dim': ('depth_interp', 'time'), 'unit': 'm', 'longname': "Thorpe Displacements"},
            "SALIN": {'var_name': 'SALIN', 'dim': ('depth_interp', 'time'), 'unit': 'PSU', 'longname': 'salinity'},
            "Cond20": {'var_name': 'Cond20', 'dim': ('depth_interp', 'time'), 'unit': 'mS/cm', 'longname': 'conductivity at 20°C'},
            "latitude": {'var_name': 'latitude', 'dim': ('time',), 'unit': '°', 'longname': 'latitude'},
            "longitude": {'var_name': 'longitude', 'dim': ('time',), 'unit': '°', 'longname': 'longitude'},
            "dist_GEF": {'var_name': 'dist_GEF', 'dim': ('time',), 'unit': 'm', 'longname': 'Distance to closest methane extraction plant'},
        }
        
        self.data = {}

    def to_netcdf(self, foldername, filename, mode='a', time_label="time",):
        log("Saving to NetCDF", indent=1)
    
        variables = self.variables
        dimensions = self.dimensions
        data = self.data

        log("Writing data to NetCDF file {}".format(filename), indent=1)
 
        nc = netCDF4.Dataset(os.path.join(foldername, filename), mode='w', format='NETCDF4')

        for key in self.general_attributes:
            setattr(nc, key, self.general_attributes[key])

        for key, values in dimensions.items():
            nc.createDimension(values['dim_name'], values['dim_size'])

        for key, values in variables.items():
            var = nc.createVariable(values["var_name"], np.float64, values["dim"], fill_value=np.nan)
            var.units = values["unit"]
            var.long_name = values["longname"]
            try:
                #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                if isinstance(data[key], str) and data[key]=='N/a':     
                    data[key]=np.nan 
                var[:] = data[key]
            except:
                breakpoint()
                nc.close()
        nc.close()
        log("netCDF file created!", indent=1)
            

