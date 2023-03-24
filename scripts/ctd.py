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
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from functions import *
from scipy import interpolate
import seawater as sw
import re as re
import matplotlib.pyplot as plt
import collections


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
            "title": "Lake Kivu CTD",
            "latitude": "-1.850964",
            "longitude": "29.208903",
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
            "SALIN": {'var_name': 'SALIN', 'dim': ('time',), 'unit': 'PSU', 'longname': 'salinity', }
        }

        self.grid_dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            "depth_ref": {'dim_name': "depth_ref", 'dim_size': None}
        }
        
        self.grid_variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            'Press': {'var_name':'Press', 'dim':('depth_ref','time'), 'unit': 'dbar', 'longname': 'pressure'},
            "depth": {'var_name': "depth", 'dim': ('depth_ref','time'), 'unit': 'm', 'longname': "Depth", },
            "depth_ref": {'var_name': "depth_ref", 'dim': ('depth_ref',), 'unit': 'm', 'longname': "Depth adjusted to reference depth"},
            'Temp': {'var_name': 'Temp', 'dim': ('depth_ref', 'time'), 'unit': 'degC', 'longname': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('depth_ref', 'time'), 'unit': 'mS/cm', 'longname': 'conductivity'},
            'Chl_A': {'var_name': 'Chl_A', 'dim': ('depth_ref', 'time'), 'unit': 'g/l', 'longname': 'chlorophyll A'},
            'Turb': {'var_name': 'Turb', 'dim': ('depth_ref', 'time'), 'unit': 'FTU', 'longname': 'Turbidity'},
            'pH': {'var_name': 'pH', 'dim': ('depth_ref', 'time'), 'unit': '_', 'longname': 'pH'},
            'sat': {'var_name': 'sat', 'dim': ('depth_ref', 'time'), 'unit': '%', 'longname': 'oxygen saturation'},
            'DO_mg': {'var_name': 'DO_mg', 'dim': ('depth_ref', 'time'), 'unit': 'mg/l', 'longname': 'oxygen concentration'},
            "rho": {'var_name': "rho", 'dim': ('depth_ref', 'time'), 'unit': 'kg/m3', 'longname': "Density", },
            "pt": {'var_name': "pt", 'dim': ('depth_ref', 'time'), 'unit': 'degC', 'longname': "Potential Temperature", },
            "prho": {'var_name': "prho", 'dim': ('depth_ref', 'time'), 'unit': 'kg/m3', 'longname': "Potential Density"},
            "thorpe": {'var_name': "thorpe", 'dim': ('depth_ref', 'time'), 'unit': 'm', 'longname': "Thorpe Displacements"},
            "SALIN": {'var_name': 'SALIN', 'dim': ('depth_ref', 'time'), 'unit': 'PSU', 'longname': 'salinity'},
            "latitude": {'var_name': 'latitude', 'dim': ('time',), 'unit': '°', 'longname': 'latitude'},
            "longitude": {'var_name': 'longitude', 'dim': ('time',), 'unit': '°', 'longname': 'longitude'},
            "dist_GEF": {'var_name': 'dist_GEF', 'dim': ('time',), 'unit': 'm', 'longname': 'Distance to closest methane extraction plant'},
        }
        
        self.data = {}
        self.grid = {}

    def read_raw_data(self, infile, max_date=datetime.utcnow(), min_date=datetime(2008, 1, 1)):
        log("Reading data from {}".format(infile), indent=1)
        try:
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

            if infile[-4:]=='.TOB':
                keyword_skip="Lines"
            elif infile[-4:]=='.cnv':
                keyword_skip="*END*"
            else:
                log("Wrong file format", indent=1)
                return False
            
            
            # Define the parameters used to read the files (rows to skip, name of columns, date_format, etc.):
            skip_rows, columns, units, valid, date_format, start_date = parse_file(infile,keyword_skip)
            if valid == False:
                log("Parse file failed.", indent=1)
                return False

            df = pd.read_csv(infile, delim_whitespace=True, header=None, skiprows=skip_rows, names=columns, engine='python', encoding="cp1252")
            df = df.drop_duplicates() # Remove duplicate rows
            if infile[-4:]=='.TOB':
                df = parse_time(df, self.variables["time"], "time", columns, units, ref_date, date_format)
            else:
                df["time"]=start_date.replace(tzinfo=timezone.utc).timestamp()+df["Minutes"]*60
                df["Cond"]=df["Cond"]/1000 # Conversion from uS/cm to mS/cm
                df["Press"]=df["Depth"]/1.019716 # Estimate of pressure [dbar] from depth values according to SeaBird software
            if math.isnan(df.Cond.iloc[-1]):
                df.drop(index=df.index[-1], axis=0, inplace=True)

            for variable in self.variables:
                if "function" in self.variables[variable]:
                    self.data[variable] = np.array(self.variables[variable]["function"](df, self.variables[variable], variable, columns, units, ref_date, date_format))
                elif variable in df.columns:
                    self.data[variable] = np.array(df[variable].values)
                else:
                    self.data[variable] = np.array([np.nan] * len(df))

            if self.data["time"][0] > max_date.timestamp() or self.data["time"][0] < min_date.timestamp():
                log("Time outside of project time range.", indent=1)
                if datetime.utcfromtimestamp(self.data["time"][0]).year==2004:
                    log("Change year 2004 into 2008.", indent=1)
                    tdate=[datetime.utcfromtimestamp(self.data["time"][i]) for i in np.arange(0,len(self.data["time"]),1)]
                    self.data["time"]=np.array([datetime(2008,tdate[i].month,tdate[i].day,tdate[i].hour,tdate[i].minute,tdate[i].second).replace(tzinfo=timezone.utc).timestamp() for i in np.arange(0,len(self.data["time"]),1)])
                else:
                    return False

            if not check_valid_profile(self.data["Press"], 3):
                log("Invalid profile", indent=1)
                return False

            return True
        except:
            log("Failed to parse raw data from file {}".format(infile), indent=1)
            return False

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
            ynew = f(xnew) # Water level at the time of the measurements
            
            # Difference between the reference water level and the actual water level 
            # (>0 if the level is lower than the reference), which must be 
            # added to the depth data to get the depth with respect to the reference
            # water level:
            self.depth_value = reference_depth - ynew

    def extract_meta_data(self, infile,):
        """"
        Function description
        Input: 
            Reads the added meta data which is in the first 15 lines of the files.
        Outputs: 
            Adds the meta data to the general_attibutes so it can be looked at in the level2A data. 
        """
        
        self.general_attributes["file_name"] = infile[infile.rfind("/")+1:]
        with open(infile, 'r', encoding="utf8", errors='ignore') as f:
            first_line = f.readline()
            if "Meta Data" in first_line: # Only for TOB files
                line_numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
                lines = []
                for i, line in enumerate(f):
                    if i in line_numbers:
                        lines.append(line.strip())
                self.general_attributes["campaign_number"] = strip_metadata(lines[0])
                self.general_attributes["profile_count"] = strip_metadata(lines[1])
                self.general_attributes["profile"] = strip_metadata(lines[2])
                self.general_attributes["date"] = strip_metadata(lines[3])
                self.general_attributes["distance_to_GEF"] = strip_metadata(lines[6])
                self.general_attributes["rope_length"] = strip_metadata(lines[7])
                self.general_attributes["max_depth"] = strip_metadata(lines[8])
                #self.general_attributes["file_name"] = strip_metadata(lines[9])
                self.general_attributes["purpose_of_sampling"] = strip_metadata(lines[10])
                self.general_attributes["pH_calibration"] = "(7): " + strip_metadata(
                    lines[11]) + " (9): " + strip_metadata(lines[12]) + " (4): " + strip_metadata(lines[13])

                latitude = float(strip_metadata(lines[4]))
                longitude = float(strip_metadata(lines[5]))
                if (-1.520405 > latitude > -2.555959) and (28.737987 < longitude < 29.501541):
                    self.general_attributes["latitude"] = latitude
                    self.general_attributes["longitude"] = longitude
                elif (1.520405 < latitude < 2.555959) and (28.737987 < longitude < 29.501541):
                    self.general_attributes["latitude"] = -latitude
                    self.general_attributes["longitude"] = longitude
                else:
                    log("Latitude and longitude fall outside lake bounds.")
            else: # SBE files
                self.general_attributes["distance_to_GEF"] = np.nan
                self.general_attributes["latitude"] = np.nan
                self.general_attributes["longitude"] = np.nan
                
                
    def extract_profile(self, remove_distance=1,press_surface=100):
        log("Extracting profile...", indent=1)
        self.data["Press"] = np.array([float(i) for i in self.data["Press"]])
        self.water_entry_index = 0
        self.submerged_index = 0
        self.bottom_of_profile_index = len(self.data["Press"])

        if not np.isnan(self.data["Cond"]).all():
            #ind_dt=10
            #t_diff=(self.data["time"][ind_dt:]-self.data["time"][:-ind_dt]) #sec
            #CTD_speed=(self.data["Press"][ind_dt:]-self.data["Press"][:-ind_dt])/t_diff # dbar/sec
           # press_speed=self.data["Press"][ind_dt:]
            #CTD_speed=CTD_speed[:np.argmax(press_speed)]
            #press_speed=press_speed[:np.argmax(press_speed)]
            # max_start=ind_dt+np.where(CTD_speed[press_speed<(min(press_speed)+5)]<0.005)[0][-1] # Last value in the upper 5 m of the water column when the CTD was stopped
            # max_start = np.where(self.data["Press"] > np.nanmin(self.data["Press"]) + 1)[0][0]# Index where pressure is 1 dbar higher than minimum
            

            diff_cond = abs(first_centered_differences(np.arange(len(self.data["Cond"])), self.data["Cond"]))
            #Use conductivity data in the surface layer (less peaks) to define the threshold:
            diff_surface=diff_cond[:np.argmax(self.data["Press"])]
            diff_surface=diff_surface[self.data["Press"][:np.argmax(self.data["Press"])]-np.nanmin(self.data["Press"])<press_surface]    
            perc_cond = np.where(diff_cond > np.percentile(diff_surface, 99))
            #perc_cond_begin = np.where(diff_cond[:max_start] > np.percentile(diff_cond, 95))

            # if len(perc_cond_begin[0]) > 0:# Increase of conductivity occurs before max_start (then take last conductivity increase before max_start)
            #     water_entry_index = perc_cond_begin[0][-1] + 1
            # else:
            #     water_entry_index = perc_cond[0][0]
            press_first_peak=self.data["Press"][perc_cond[0][0]]-np.nanmin(self.data["Press"])
            press_last_peak=self.data["Press"][perc_cond[0][-1]]-np.nanmin(self.data["Press"])
            if perc_cond[0][0]>=1 and press_first_peak<1: # First conductivity peak is near the surface
                self.air_press = np.percentile(self.data["Press"][:perc_cond[0][0]+1],0.05)
            elif perc_cond[0][-1]<len(self.data["Press"])-1 and press_last_peak<1: # Last conductivity peak is near the surface
                self.air_press = np.percentile(self.data["Press"][perc_cond[0][-1]:],0.05)
            elif perc_cond[0][0]==0 or perc_cond[0][-1]==len(self.data["Press"])-1: # No data point in the air
                breakpoint()
                log('No data point above conductivity peak')
                return False
            else: #There is no conductivity peak: remove the profile
                breakpoint()
                log("No conductivity peak detected (first peak: "+str(press_first_peak)+" dbar, last peak: "+str(press_last_peak)+" dbar)", indent=1)    
                return False
            
            water_entry_index=np.where(self.data["Press"]>self.air_press+1)[0][0] # Always take water entry index as 1 m below air pressure to remove the upper 1m
            
            submerged_index = perc_cond[0][0]
            for i in range(len(perc_cond[0])-1):# For each index of the conductivity peak
                if perc_cond[0][i+1] - perc_cond[0][i] != 1: # More than one index of difference, i.e., different conductivty peak
                    submerged_index = perc_cond[0][i] # Save the index of the 2nd conductivty peak
                    break
            if len(self.data["Press"]) > water_entry_index > 0: # water_entry_index=0 otherwise (initial default value)
                self.water_entry_index = water_entry_index - 1
            if len(self.data["Press"]) > submerged_index > 0:
                self.submerged_index = submerged_index + 1
        
        # Remove a given distance above the maximum pressure:
        self.bottom_of_profile_index = np.where(self.data["Press"][0:np.argmax(self.data["Press"])]<=np.max(self.data["Press"])-remove_distance)[0][-1]
        #self.bottom_of_profile_index = np.argmax(self.data["Press"]) - remove_timesteps
        
        # if self.water_entry_index > 0:
        #     self.air_press = np.nanmean(self.data["Press"][0:self.water_entry_index])
        # else:
        #     self.air_press = np.nanmin(self.data["Press"][:self.bottom_of_profile_index])

        #self.air_press = np.nanmin(self.data["Press"][:self.bottom_of_profile_index]) # Always take the minimum pressure as the air pressure
        #self.air_press = np.percentile(self.data["Press"][0:max_start],0.05)
        
        if (self.air_press-np.nanmin(self.data["Press"][:self.bottom_of_profile_index]))>0.5: # Large difference between estimated air pressure and min pressure
            print('Difference of air pressures: '+str((self.air_press-np.nanmin(self.data["Press"][:self.bottom_of_profile_index]))))    
            breakpoint()
        return True

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
                    if simple: #Always used
                        self.data[name] = qualityassurance(np.array(self.data[key]), np.array(self.data["time"]), **quality_assurance_dict[key]["simple"])
                        if "std_moving" in quality_assurance_dict[key].keys(): # Outlier removal based on std and moving average
                            param_outliers=quality_assurance_dict[key]["std_moving"]
                            qa_bool=qa_std_moving(np.array(self.data[key]), window_size=param_outliers["window_size"], factor=param_outliers["factor"], prior_flags=self.data[name].astype(bool))
                            self.data[name]=qa_bool.astype(int)
                    else:
                        quality_assurance_all = dict(quality_assurance_dict[key]["simple"], **quality_assurance_dict[key]["advanced"])
                        self.data[name] = qualityassurance(np.array(self.data[key]), np.array(self.data["time"]), **quality_assurance_all)
                    if key != "time":
                        self.data[name] = self.quality_assurance_ctd(self.data[name])

    def quality_assurance_ctd(self, qa): # To remove data before water entry and after reaching the bottom
        #qa: quality assurance values (0 or 1)
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
            if os.path.isfile(out_file): # File has already been created
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
                        #if key not in dimensions and key != "depth": 
                        if key not in dimensions: 
                            var = nc.variables[key]
                            # if title=="L2B":
                            #     print(key)
                            #     breakpoint()
                            try:
                                #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                                if isinstance(data[key], str) and data[key]=='N/a':      
                                    data[key]=np.nan
                            except:
                                breakpoint()
                                nc.close()
                            try:
                                if len(var.shape)==1:
                                    end=len(var[:]) - 1
                                else:
                                    end = len(var[:][0]) - 1
                            except:
                                print(var)
                            if idx != end: # New profile was taken before the previous last profile --> needs to be inserted
                                if len(var.shape)==1:
                                    var[end] = data[key]
                                    var[:] = var[np.insert(np.arange(end), idx, end)]
                                else:
                                    var[:, end] = data[key]
                                    var[:] = var[:, np.insert(np.arange(end), idx, end)]
                            else:
                                if len(var.shape)==1:
                                    var[idx] = data[key]
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
                    try:
                        #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                        if isinstance(data[key], str) and data[key]=='N/a':     
                            data[key]=np.nan
                        if len(values["dim"]) == 1:
                            var[:] = data[key]
                        elif len(values["dim"]) == 2:
                            var[:, 0] = data[key]
                    except:
                        breakpoint()
                        nc.close()
                nc.close()

            start = start + td

    def profile_to_timeseries_grid(self, vars_nointerp,time_label="time"):
        log("Resampling profile to fixed grid...", indent=2)
        self.grid["depth_ref"] = self.fixed_depths_ref
        self.grid["time"] = [np.nanmin(self.data[time_label])]
        for key, values in self.grid_variables.items():
            if key not in self.grid_dimensions and key not in vars_nointerp: # Apply the interpolation for variables that are not dimensions and that are not listed in vars_nointerp
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
            if "_qual" not in var: # Apply mask on variables of "data"
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
        
        log("Loading gas data...", indent=2)
        df_gas=pd.read_excel('..\data\gas_profile\Gas_profile.xlsx',names=['Depth','CH4','CH4_err','CO2','CO2_err'])
        
        
        try:
            log("Calculating density...", indent=2)
            self.data["rho"] = np.asarray([1000] * len(data["Press"]))
            #self.data["rho"] = density(data["Temp"], self.data["SALIN"])
            rho_TS = density(temperature=data["Temp"], salinity=self.data["SALIN"],press=self.data["Press"])
            depth_TS=1e4 * data["adj_press"] / rho_TS / sw.g(lat)
            C_CH4=np.interp(depth_TS, df_gas["Depth"][~np.isnan(df_gas["CH4"])], df_gas["CH4"][~np.isnan(df_gas["CH4"])]*16/1000) # g/L
            C_CO2=np.interp(depth_TS, df_gas["Depth"][~np.isnan(df_gas["CO2"])], df_gas["CO2"][~np.isnan(df_gas["CO2"])]*44/1000) # g/L
            self.data["rho"] = density(temperature=data["Temp"], salinity=self.data["SALIN"],C_CH4=C_CH4,C_CO2=C_CO2)
        except Exception :
            log("Failed to calculate density", indent=2)
            return False

        log("Calculating depth...", indent=2)
        rho_p=density(temperature=data["Temp"], salinity=self.data["SALIN"],press=self.data["Press"],C_CH4=C_CH4,C_CO2=C_CO2)
        self.data["depth"] = 1e4 * data["adj_press"] / rho_p / sw.g(lat)
        log("Calculating depth_ref...", indent=2)
        self.data["depth_ref"] = (1e4 * data["adj_press"] / self.data["rho"] / sw.g(lat)) + self.depth_value
        b=(self.data["depth_ref"])
        try:
            log("Calculating potential temperature...", indent=2)
            self.data["pt"]  = potential_temperature_sw(S=self.data["SALIN"], T=data["Temp"], p=data["adj_press"], p_ref=0)
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
