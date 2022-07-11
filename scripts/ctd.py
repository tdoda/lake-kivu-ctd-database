# -*- coding: utf-8 -*-
import os
import json
import netCDF4
import dateparser
import numpy as np
import pandas as pd
import math
from copy import deepcopy
from envass import qualityassurance
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functions import copyFiles,is_number,check_valid_profile,fixed_grid_resample_guide,resample,index_of_max,position_in_array,round_to_days,advanced_quality_flags,json_converter,log,error,find_closest_index,is_number,isnt_number,first_centered_differences,default_salinity_temperature,salinity,density,Gamma_adiabatic,mask_single_data,potential_temperature,oxygen_saturation,parse_file,rename_duplicates,check_variable,parse_time,parse_chl
from scipy import interpolate
import seawater as sw
import re as re

class ctd:
    def __init__(self):
        self.water_entry_index = False
        self.bottom_of_profile_index = False
        self.air_press = False
        self.submerged_index = False
        self.depth_value = 0
        self.fixed_depths_ref = np.concatenate((np.linspace(0, 50, 501), np.linspace(50.5, 320, 540)))
        self.general_attributes = {
            "institution": "Eawag",
            "source": "Lake Kivu Monitoring Program",
            "references": "james.runnalls@eawag.ch",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "CTD profiles for Lake Kivu ",
            "title": "Lake Kivu CTD"
        }

        self.dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None}
        }

        self.variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            'Press': {'var_name':'Press', 'dim':('time',), 'unit': 'dbar', 'longname': 'pressure'},
            'Temp': {'var_name':'Temp', 'dim':('time',), 'unit': 'degC', 'longname': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('time',), 'unit': 'mS/cm', 'longname': 'conductivity'},
            'Chl_A': {'var_name': 'Chl_A', 'dim': ('time',), 'unit': 'g/l', 'longname': 'chlorophyll A', "function": parse_chl},
            'Turb': {'var_name': 'Turb', 'dim': ('time',), 'unit': 'FTU', 'longname': 'Turbidity'},
            'pH': {'var_name': 'pH', 'dim': ('time',), 'unit': '_', 'longname': 'pH'},
            'sat': {'var_name': 'sat', 'dim': ('time',), 'unit': '%', 'longname': 'oxygen saturation'},
            'DO_mg': {'var_name': 'DO_mg', 'dim': ('time',), 'unit': 'mg/l', 'longname': 'oxygen concentration'},
            }

        self.derived_variables = { 
            "rho": {'var_name': "rho", 'dim': ('time',), 'unit': 'kg/m3', 'longname': "Density", },
            "depth": {'var_name': "depth", 'dim': ('time',), 'unit': 'm', 'longname': "Depth", },
            "depth_ref": {'var_name': "depth_ref", 'dim': ('time',), 'unit': 'm', 'longname': "Depth adjusted to reference depth"},
            "pt": {'var_name': "pt", 'dim': ('time',), 'unit': 'degC', 'longname': "Potential Temperature", },
            "prho": {'var_name': "prho", 'dim': ('time',), 'unit': 'kg/m3', 'longname': "Potential Density", },
            "thorpe": {'var_name': "thorpe", 'dim': ('time',), 'unit': 'm', 'longname': "Thorpe Displacements", },
            "SALIN": {'var_name': 'SALIN', 'dim': ('time',), 'unit': ['PSU', 'ppt'], 'longname': 'salinity', }
        }

        self.grid_dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            "depth_ref": {'dim_name': "depth_ref", 'dim_size': None}
        }
        
        self.grid_variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            "depth": {'var_name': "depth", 'dim': ('depth_ref',), 'unit': 'm', 'longname': "Depth", },
            "depth_ref": {'var_name': "depth_ref", 'dim': ('depth_ref',), 'unit': 'm', 'longname': "Depth adjusted to reference depth"},
            'Temp': {'var_name': 'Temp', 'dim': ('depth_ref', 'time'), 'unit': ('degC',"?C"), 'longname': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('depth_ref', 'time'), 'unit': 'mS/cm', 'longname': 'conductivity'},
            'Chl_A': {'var_name': 'Chl_A', 'dim': ('depth_ref', 'time'), 'unit': ('g/l', 'g/L') , 'longname': 'chlorophyll A'},
            'Turb': {'var_name': 'Turb', 'dim': ('depth_ref', 'time'), 'unit': 'FTU', 'longname': 'Turbidity'},
            'pH': {'var_name': 'pH', 'dim': ('depth_ref', 'time'), 'unit': ('_','0_14'), 'longname': 'pH'},
            'sat': {'var_name': 'sat', 'dim': ('depth_ref', 'time'), 'unit': '%', 'longname': 'oxygen saturation'},
            'DO_mg': {'var_name': 'DO_mg', 'dim': ('depth_ref', 'time'), 'unit': 'mg/l', 'longname': 'oxygen concentration'},
            "rho": {'var_name': "rho", 'dim': ('depth_ref', 'time'), 'unit': 'kg/m3', 'longname': "Density", },
            "pt": {'var_name': "pt", 'dim': ('depth_ref', 'time'), 'unit': 'degC', 'longname': "Potential Temperature", },
            "prho": {'var_name': "prho", 'dim': ('depth_ref', 'time'), 'unit': 'kg/m3', 'longname': "Potential Density"},
            "thorpe": {'var_name': "thorpe", 'dim': ('depth_ref', 'time'), 'unit': 'm', 'longname': "Thorpe Displacements"},
            "SALIN": {'var_name': 'SALIN', 'dim': ('depth_ref', 'time'), 'unit': ['PSU', 'ppt'], 'longname': 'salinity'},
        }
        
        self.data = {}
        self.grid = {}

    def read_raw_data(self, infile,):
        log("Reading data from {}".format(infile), indent=1)
        with open(infile, encoding="utf8", errors='ignore') as f:
            lines = f.readlines()
        try:
            ref_date = datetime.timestamp(dateparser.parse(lines[2]))
            log("Detected reference date {} on line 2".format(dateparser.parse(lines[2])), indent=2)
        except:
            log("Unable to convert date fom line 2", indent=2)
            ref_date = False
        if ref_date == False:
            try:
                ref_date = datetime.timestamp(dateparser.parse(lines[19]))
                log("Detected reference date {} on line 20".format(dateparser.parse(lines[19])), indent=2)
            except:
                log("Unable to convert date from line 20", indent=2)
                ref_date = False

        skip_rows, columns, units, valid, date_format = parse_file(infile, "Lines")

        if valid == False:
            return False

        df = pd.read_csv(infile, delim_whitespace=True, header=None, skiprows=skip_rows, names=columns, engine='python', encoding="cp1252")
        df = parse_time(df, self.variables["time"], "time", columns, units, ref_date, date_format)

        if math.isnan(df.Cond.iloc[-1]):
            df.drop(index=df.index[-1], axis=0, inplace=True)

        for variable in self.variables:
            if "function" in self.variables[variable]:
                self.data[variable] = np.array(self.variables[variable]["function"](df, self.variables[variable], variable, columns, units, ref_date, date_format))
            elif variable in df.columns:
                self.data[variable] = np.array(df[variable].values)
            else:
                self.data[variable] = np.array([np.nan] * len(df))

        if self.data["time"][0] > datetime.utcnow().timestamp():
            return False

        if not check_valid_profile(self.data["Press"], 3): 
            return False
        
        return True

    def extract_water_level(self, path, reference_depth, time_label="time"):
        """"
        Function description
        Inputs:
            path: Link to the file with lake level measurements
            reference_depth: Set to 1462 m.a.s.l.
            time_label: time
        Outputs: 
            self.depth_value: Difference between the reference_depth and the lake level data for the date of the CTD-profile. 
        """
        xnew = self.data[time_label][0]
        if ".txt" in path:
            headers = ['Date', 'Waterlevel', 'Error_range']
            df1 = pd.read_csv(path, skiprows=15, delimiter=' ', names=headers)
            df1['seconds_since_1970'] = list(pd.to_datetime(df1["Date1"], format= "%Y-%m-%d", dayfirst=True).values.astype(float) / 10 ** 9)
            x= df1["seconds_since_1970"]
            y= df1["Waterlevel"]
            f = interpolate.interp1d(x, y)
            ynew = f(xnew)  
            self.depth_value = reference_depth - ynew  
        elif ".csv" in path:
            headers = ['Date', 'Waterlevel']
            df1 = pd.read_csv(path,delimiter=';', skiprows=1, names=headers)
            df1['seconds_since_1970'] = list(pd.to_datetime(df1["Date"], format= "%d.%m.%Y", dayfirst=True).values.astype(float) / 10 ** 9)
            x= df1["seconds_since_1970"]
            y= df1["Waterlevel"]
            f = interpolate.interp1d(x, y)
            ynew = f(xnew)  
            self.depth_value = reference_depth - ynew
        elif ".json" in path:
            with open(path) as f:
                data1=json.load(f)
            Date1 = [i['datetime'] for i in data1["data"]]
            Waterlevel = [i['water_surface_height_above_reference_datum'] for i in data1['data']]
            df1 = pd.DataFrame({'Date1':Date1, 'Waterlevel':Waterlevel})
            df1['seconds_since_1970'] = list(pd.to_datetime(df1["Date1"], format= "%Y/%m/%d", dayfirst=True).values.astype(float) / 10 ** 9)
            x= df1["seconds_since_1970"]
            y= df1["Waterlevel"]
            f = interpolate.interp1d(x, y)
            ynew = f(xnew)  
            self.depth_value = reference_depth - ynew

    def extract_meta_data(self, infile,):
        """"
        Function description
        Input: 
            Reads the added meta data which is in the first 15 lines of the files.
        Outputs: 
            Adds the meta data to the general_attibutes so it can be looked at in the level2A data. 
        """
        
        with open(infile, 'r', encoding="utf8", errors='ignore') as f:
            first_line = f.readline()
            if "Meta Data" in first_line:
                line_numbers = [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
                lines = []
                for i, line in enumerate(f):
                    if i in line_numbers:
                        lines.append(line.strip())

                self.general_attributes["campaign_number"]     = lines[0].replace(" ", "")
                self.general_attributes["profile_count"]       = lines[1].replace(" ", "")
                self.general_attributes["profile"]             = lines[2].replace(" ", "")
                self.general_attributes["date"]                = lines[3].replace(" ", "")
                self.general_attributes["latitude"]            = lines[4].replace(" ", "")
                self.general_attributes["longitude"]           = lines[5].replace(" ", "")
                self.general_attributes["distance_to_GEF"]     = lines[6].replace(" ", "")
                self.general_attributes["rope_length"]         = lines[7].replace(" ", "")
                self.general_attributes["max_depth"]           = lines[8].replace(" ", "")
                self.general_attributes["file_name"]           = lines[9].replace(" ", "")
                self.general_attributes["purpose_of_sampling"] = lines[10].replace(" ", "")
                self.general_attributes["pH_calibration"]      = (lines[11].replace(" ", ""),
                                                                  lines[12].replace(" ", ""),
                                                                  lines[13].replace(" ", ""))      
                pattern     = ".*" + ":"
                latitude    = lines[4].replace(" ", "")
                latitude    = float(re.sub(pattern, '', latitude))
                longitude   = lines[5].replace(" ", "")
                longitude   = float(re.sub(pattern, '', longitude))
                self.data["lon"]=longitude
                self.data["lat"]=latitude


                    
    def extract_profile(self, remove_timesteps=3):
        log("Extracting profile...", indent=1)
        self.data["Press"] = np.array([float(i) for i in self.data["Press"]])
        self.water_entry_index = 0
        self.submerged_index = 0
        self.bottom_of_profile_index = len(self.data["Press"])

        if not np.isnan(self.data["Cond"]).all():
            diff_cond = first_centered_differences(np.arange(len(self.data["Cond"])), self.data["Cond"])
            perc_cond = np.where(diff_cond > np.percentile(diff_cond, 85))
            water_entry_index = perc_cond[0][0]
            submerged_index = perc_cond[0][0]
            for i in range(len(perc_cond[0])-1):
                if perc_cond[0][i+1] - perc_cond[0][i] != 1:
                    submerged_index = perc_cond[0][i]
                    break
            if len(self.data["Press"]) > water_entry_index > 0:
                self.water_entry_index = water_entry_index - 1
            if len(self.data["Press"]) > submerged_index > 0:
                self.submerged_index = submerged_index + 1
                

        self.bottom_of_profile_index = np.argmax(self.data["Press"]) - remove_timesteps

        if self.water_entry_index > 0:
            self.air_press = np.nanmean(self.data["Press"][0:self.water_entry_index])
        else:
            self.air_press = np.nanmin(self.data["Press"][:self.bottom_of_profile_index])

    def quality_assurance(self, file_path, simple=True):
        log("Applying quality assurance", indent=1)
        quality_assurance_dict = json_converter(json.load(open(file_path)))
        for key, values in self.variables.copy().items():
            if ("_qual" not in key)and(key in quality_assurance_dict):
                if (quality_assurance_dict[key]["advanced"]) or (quality_assurance_dict[key]["simple"]):
                    name = key + "_qual"
                    self.variables[name] = {'var_name': name, 'dim': values["dim"],
                                            'unit': '0 = nothing to report, 1 = more investigation',
                                            'longname': name, }
                    if simple:
                        self.data[name] = qualityassurance(np.array(self.data[key]), np.array(self.data["time"]), **quality_assurance_dict[key]["simple"])
                    else:
                        quality_assurance_all = dict(quality_assurance_dict[key]["simple"], **quality_assurance_dict[key]["advanced"])
                        self.data[name] = qualityassurance(np.array(self.data[key]), np.array(self.data["time"]), **quality_assurance_all)
                    if key != "time":
                        self.data[name] = self.quality_assurance_ctd(self.data[name])

    def quality_assurance_ctd(self, qa):
        if self.bottom_of_profile_index:
            qa[self.bottom_of_profile_index:] = 1

        if self.water_entry_index:
            qa[:self.water_entry_index] = 1

        return qa

    def to_netcdf(self, folder, title,  output_period="profile", mode='a', time_label="time", grid=False,):
        log("Saving to NetCDF", indent=1)
        if not os.path.exists(folder):
            os.makedirs(folder)

        if grid:
            variables = self.grid_variables
            dimensions = self.grid_dimensions
            data = self.grid
        else:
            variables = self.variables
            dimensions = self.dimensions
            data = self.data

        time_arr = data[time_label]
        dt_min = datetime.utcfromtimestamp(np.nanmin(time_arr))
        dt_max = datetime.utcfromtimestamp(np.nanmax(time_arr))
    
        if output_period == "weekly":
            start = (dt_min - timedelta(days=dt_min.weekday())).replace(hour=0, minute=0, second=0)
            td = timedelta(weeks=1)
        elif output_period == "monthly":
            start = dt_min.replace(day=1, hour=0, minute=0, second=0)
            td = relativedelta(months=+1)
        elif output_period == "yearly":
            start = dt_min.replace(month=1, day=1, hour=0, minute=0, second=0)
            td = start.replace(year=start.year+1)-start
        elif output_period == "profile":
            start = dt_min
            td = dt_max-dt_min
        else:
            log("Output periods {} not defined.".format(output_period))
            return

        while start < dt_max:
            end = start + td
            s = datetime.timestamp(start)
            e = datetime.timestamp(end)

            filename = "{}_{}.nc".format(title, start.strftime('%Y%m%d_%H%M%S'))
            out_file = os.path.join(folder, filename)
            log("Writing {} data from {} until {} to NetCDF file {}".format(title, start, end, filename), 1)

            if os.path.isfile(out_file):
                nc = netCDF4.Dataset(out_file, mode=mode, format='NETCDF4')
                nc_time = nc.variables[time_label]

                if time_arr[0] in nc_time:
                    log("Duplicated run, no data added", 2)
                    nc.close()
                    start = start + td
                    continue
                else:
                    idx = position_in_array(nc_time, time_arr[0])
                    nc_time[:] = np.insert(nc_time[:], idx, time_arr[0])
                    for key, values in variables.items():
                        if key not in dimensions and key != "depth": 
                            var = nc.variables[key]
                            try:
                                end = len(var[:][0]) - 1
                            except:
                                print(var)
                            if idx != end:
                                var[:, end] = data[key]
                                var[:] = var[:, np.insert(np.arange(end), idx, end)]
                            else:
                                var[:, idx] = data[key]
                    nc.close()

            else:
                nc = netCDF4.Dataset(out_file, mode='w', format='NETCDF4')

                for key in self.general_attributes:
                    setattr(nc, key, self.general_attributes[key])

                for key, values in dimensions.items():
                    nc.createDimension(values['dim_name'], values['dim_size'])

                for key, values in variables.items():
                    var = nc.createVariable(values["var_name"], np.float64, values["dim"], fill_value=np.nan)
                    var.units = values["unit"]
                    var.long_name = values["longname"]
                    if len(values["dim"]) == 1:
                        var[:] = data[key]
                    elif len(values["dim"]) == 2:
                        var[:, 0] = data[key]
            
                nc.close()

            start = start + td

    def profile_to_timeseries_grid(self, time_label="time"):
        log("Resampling profile to fixed grid...", indent=2)
        self.grid["depth_ref"] = self.fixed_depths_ref
        self.grid["time"] = [np.nanmin(self.data[time_label])]
        for key, values in self.grid_variables.items():
            if key not in self.grid_dimensions:
                mask = (~np.isnan(self.data[key])) & (~np.isnan(self.data["depth_ref"]))
                depths_ref = self.data["depth_ref"][mask]
                data = self.data[key][mask]
                if len(data) < 50:
                    self.grid[key] = np.asarray([np.nan] * len(self.fixed_depths_ref))
                else:
                    self.grid[key] = np.interp(self.fixed_depths_ref, depths_ref, data, left=np.nan, right=np.nan)

    def derive_variables(self, lat, alt, y_cond=0.874e-3, beta=0.807e-3, ):
        log("Calculating derived variables...", indent=1)
        data = deepcopy(self.data)
        log("Masking variables for calculations", indent=2)
        for var in self.variables:
            if "_qual" not in var:
                idx = data[var+"_qual"] > 0
                float_data = data[var].astype(float)
                float_data[idx] = np.nan
                data[var] = float_data.copy()
                                
        data["adj_press"] = data["Press"] - self.air_press
        threshold = data["Temp"].shape[0] * 0.9
        if sum(np.isnan(data["Temp"])) > threshold or sum(np.isnan(data["Cond"])) > threshold or \
                sum(np.isnan(data["adj_press"])) > threshold:
            log("Not enough valid parameters for derived variables.", indent=2)
            return False
        else:
            self.variables.update(self.derived_variables)

        try:
            log("Calculating salinity...", indent=2)
            self.data["SALIN"] = salinity(data["Temp"], data["Cond"], y_cond, temperature_func=default_salinity_temperature)
        except Exception:
            log("Failed to calculate salinity", indent=2)
            return False
        
        try:
            log("Calculating density...", indent=2)
            self.data["rho"] = np.asarray([1000] * len(data["Press"]))
            self.data["rho"] = density(data["Temp"], self.data["SALIN"])
        except Exception :
            log("Failed to calculate density", indent=2)
            return False

        log("Calculating depth...", indent=2)
        self.data["depth"] = 1e4 * data["adj_press"] / self.data["rho"] / sw.g(lat)
        a=(self.data["depth"])
    
        log("Calculating depth_ref...", indent=2)
        self.data["depth_ref"] = (1e4 * data["adj_press"] / self.data["rho"] / sw.g(lat)) + self.depth_value
        b=(self.data["depth_ref"])

        try:
            log("Calculating potential temperature...", indent=2)
            self.data["pt"] = potential_temperature(data["Temp"], self.data["SALIN"], data["adj_press"], self.data["depth"], lat) 
        except Exception:
            self.data["pt"] = np.asarray([np.nan] * len(data["time"]))
            log("Failed to calculate potential temperature")

        try:
            log("Calculating potential density...", indent=2)
            self.data["prho"] = density(self.data["pt"], self.data["SALIN"])
        except Exception:
            log("Failed to calculate potential density", indent=2)

        try:
            log("Calculating oxygen saturation...", indent=2)
            self.data["sat"] = oxygen_saturation(self.data["pt"], self.data["SALIN"], alt, lat)
        except Exception :
            log("Failed to replace oxygen saturation", indent=2)

        try:
            log("Calculating Thorpe Dispacements...", indent=2)
            sorted_pt = np.argsort(self.data["pt"])[::-1]
            self.data["thorpe"] = -(self.data["depth"] - self.data["depth"][sorted_pt]) 
        except Exception :
            log("Failed to calculate Thorpe Displacements", indent=2)

        return True
        
    def mask_data(self):
        for var in self.variables:
            if "_qual" not in var:
                idx = self.data[var+"_qual"] > 0
                self.data[var][idx] = np.nan               

    def read_processed_data(self, file):
        self.data = netCDF4.Dataset(file, 'r').variables
        for key in self.data.keys():
            self.data[key] = self.data[key][:]
