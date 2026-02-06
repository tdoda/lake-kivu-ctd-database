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
from datetime import datetime, timedelta, timezone, UTC
from dateutil.relativedelta import relativedelta
from functions import *
from scipy import interpolate
import gsw
import re as re



class ctd:
    def __init__(self,printlog=False):
        self.printlog=printlog
        self.water_entry_index = False
        self.bottom_of_profile_index = False
        self.air_press = False
        self.cond_peak_first=False
        self.cond_peak_last=False
        self.air_meas=False
        self.submerged_index = False
        self.depth_value = 0
        #self.fixed_depths_ref = np.concatenate((np.linspace(0, 50, 501), np.linspace(50.5, 320, 540)))
        # self.fixed_depths_ref = np.arange(0,320,0.1) # CEll size of 10 cm
        self.fixed_depths_ref = np.arange(0,480,0.2) # CEll size of 20 cm
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
            'time': {'dim_name': 'time', 'dim_size': None}
        }

        self.variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            'Press': {'var_name':'Press', 'dim':('time',), 'unit': 'dbar', 'longname': 'pressure'},
            'Depth_KW': {'var_name':'Depth_KW', 'dim':('time',), 'unit': 'm', 'longname': 'depth provided by Kivuwatt'},
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
            "Cond20": {'var_name': 'Cond20', 'dim': ('time',), 'unit': 'mS/cm', 'longname': 'conductivity at 20°C'},
            "SALIN": {'var_name': 'SALIN', 'dim': ('time',), 'unit': 'PSU', 'longname': 'salinity', }
        }

        self.grid_dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            "depth_interp": {'dim_name': "depth_interp", 'dim_size': None}
        }
        
        self.grid_variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            'Press': {'var_name':'Press', 'dim':('depth_interp','time'), 'unit': 'dbar', 'longname': 'pressure'},
            'Depth_KW': {'var_name':'Depth_KW', 'dim':('depth_interp','time'), 'unit': 'm', 'longname': 'depth provided by Kivuwatt'},
            "depth": {'var_name': "depth", 'dim': ('depth_interp','time'), 'unit': 'm', 'longname': "Depth", },
            "depth_interp": {'var_name': "depth_interp", 'dim': ('depth_interp',), 'unit': 'm', 'longname': "Interpolated depth"},
            "depth_ref": {'var_name': "depth_ref", 'dim': ('depth_interp',), 'unit': 'm', 'longname': "Depth adjusted to reference depth"},
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
        
      
        self.comb_variables = {
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
            "data_type": {'var_name': 'data_type', 'dim': ('time',), 'unit': '0=REMA, 1=Kivuwatt', 'longname': 'Data type, either REMA or Kivuwatt profiles'},
        }
        
        self.data = {}
        self.grid = {}
        self.comb_data = {}
    def show_output(self,printlog):
        self.printlog=printlog
    
    def read_raw_data(self, infile, max_date=datetime.utcnow(), min_date=datetime(2008, 1, 1)):
        log("Reading data from {}".format(infile), indent=1,printlog=self.printlog)
        try:
            with open(infile, encoding="utf8", errors='ignore') as f:
                lines = f.readlines()
            try:
                ref_date = datetime.timestamp(dateparser.parse(lines[2]))
                log("Detected reference date {} on line 2".format(dateparser.parse(lines[2])), indent=2,printlog=self.printlog)
            except:
                log("Unable to convert date fom line 2", indent=2,printlog=self.printlog)
                ref_date = False
            if ref_date == False:
                try:
                    for k in np.arange(len(lines)):
                        if '.SPJ' in lines[k]:
                            ref_date = datetime.timestamp(dateparser.parse(lines[k+1]))
                            break
                    log("Detected reference date {}".format(dateparser.parse(lines[k+1])), indent=2,printlog=self.printlog)
                except:
                    log("Unable to get reference date", indent=2,printlog=self.printlog)
                    ref_date = False
            if infile[-4:]=='.TOB':
                keyword_skip="Lines"
            elif infile[-4:]=='.cnv':
                keyword_skip="*END*"
            else:
                log("Wrong file format", indent=1,printlog=self.printlog)
                return False
        
            # Define the parameters used to read the files (rows to skip, name of columns, starting date, etc.):
            skip_rows, columns, units, valid, start_date, time_interval = parse_file(infile,keyword_skip)
            if valid == False:
                log("Parse file failed (not enough data points in the file)", indent=1,printlog=self.printlog)
                return False

            df = pd.read_csv(infile, sep='\s+', header=None, skiprows=skip_rows, names=columns, engine='python', encoding="cp1252")
            df = df.drop_duplicates() # Remove duplicate rows
            if infile[-4:]=='.TOB':
                df = parse_time(df, self.variables["time"], "time", columns, units, ref_date)
            else:
                if "Minutes" in df.columns:
                    df["time"]=start_date.replace(tzinfo=timezone.utc).timestamp()+df["Minutes"]*60
                elif ~np.isnan(time_interval):
                    df["time"]=start_date.replace(tzinfo=timezone.utc).timestamp()+time_interval*np.arange(df.shape[0])
                else:
                    print('Time not available for {}'.format(infile))
                    df["time"]=np.full((df.shape[0],),np.nan)
        
                df["Cond"]=df["Cond"]/1000 # Conversion from uS/cm to mS/cm
                
                df["Press"]=df["Depth"]/1.019716 # Estimate of pressure [dbar] from depth values according to SeaBird software
            if math.isnan(df.Cond.iloc[-1]):
                df.drop(index=df.index[-1], axis=0, inplace=True)
            for variable in self.variables:
                if variable in df.columns:
                    if "function" in self.variables[variable]: # If a specific function is defined to parse the variable, use it (e.g., for chlorophyll)
                        self.data[variable] = np.array(self.variables[variable]["function"](df, variable, columns, units))
                    else:
                        self.data[variable] = np.array(df[variable].values)
                else:
                    self.data[variable] = np.array([np.nan] * len(df))

            if self.data["time"][0] > max_date.timestamp() or self.data["time"][0] < min_date.timestamp():
                log("Time outside of project time range.", indent=1,printlog=self.printlog)
                if datetime.fromtimestamp(self.data["time"][0],UTC).year==2004 and infile[infile.rfind('/')+1:infile.rfind('/')+3]=='08':
                    log("Change year 2004 into 2008.", indent=1,printlog=self.printlog)
                    tdate=[datetime.fromtimestamp(self.data["time"][i],UTC) for i in np.arange(0,len(self.data["time"]),1)]
                    self.data["time"]=np.array([datetime(2008,tdate[i].month,tdate[i].day,tdate[i].hour,tdate[i].minute,tdate[i].second).replace(tzinfo=timezone.utc).timestamp() for i in np.arange(0,len(self.data["time"]),1)])
                else:
                    return False


            if not check_valid_profile(self.data["Press"], 3):
                log("Invalid profile", indent=1,printlog=self.printlog)
                return False

            return True
        except Exception as e:
            log("Failed to parse raw data from file {}".format(infile), indent=1,printlog=self.printlog)
            if os.path.exists(infile[:infile.rfind(".")]+'_v2'+infile[infile.rfind("."):]): # A second version of the file exists 
                log("A second version of the file exists, try to read that one (not done now): {}".format(infile[:infile.rfind(".")]+'_v2'+infile[infile.rfind("."):]), indent=1,printlog=self.printlog)
            
            return False
        
    def extract_meta_data_Kivuwatt(self, infile,):
        """"
        Function description: read the metadata file and add it to the general attributes.
        Input: 
            Metadata file
        Output: 
            None
        """
        log("Reading metadata...",indent=1,printlog=self.printlog)
        df_meta=pd.read_csv(infile,sep=',',encoding='ISO-8859-1',header=0,names=['Profile_count','Date','Lat','Lon','Probe','Distance_GEF'],
                              skiprows=[1],dtype={'Date':str})
        self.general_attributes["profile_count"] = df_meta["Profile_count"].values
        self.general_attributes["date"] = df_meta["Date"].values
        self.general_attributes["distance_to_GEF"] = df_meta["Distance_GEF"].values
        self.general_attributes["latitude"] = df_meta["Lat"].values
        self.general_attributes["longitude"] = df_meta["Lon"].values

    def split_profiles_Kivuwatt(self, df,CTD_meta,kprof,multip_cond=1,remove_botdist=1,remove_topdist=1,press_to_depth_factor=np.nan,):
        ind_meta=np.where(CTD_meta.general_attributes["profile_count"]==kprof)[0][0]
        bool_df=df["Profile"]==kprof
        date_str=CTD_meta.general_attributes["date"][ind_meta]
        self.general_attributes["profile_count"] = kprof
        self.general_attributes["date"] = date_str
        self.general_attributes["distance_to_GEF"] = CTD_meta.general_attributes["distance_to_GEF"][ind_meta]
        self.general_attributes["latitude"] = CTD_meta.general_attributes["latitude"][ind_meta]
        self.general_attributes["longitude"] = CTD_meta.general_attributes["longitude"][ind_meta]
      
        try: 
            # Convert time into timestamps
            date_str=CTD_meta.general_attributes["date"][ind_meta]
            date_num=pd.to_datetime(date_str+' '+df.loc[bool_df,"Hour"],format='%m/%d/%Y %H:%M:%S').astype(np.int64) // 10 ** 9
            df_prof=df.loc[bool_df,:]
            df_prof.insert(len(df_prof.columns),"Datetime",date_num)
            
            # Compute averages every second:
            df_prof=df_prof.groupby(by="Datetime").mean(numeric_only=True)
               
            for variable in self.variables: 
                if variable in df_prof.columns: 
                    #data_val = np.array(df.loc[bool_df,variable].values)
                    if variable=='Cond':
                        data_val = np.array(df_prof.loc[:,variable].values*multip_cond)
                    else:
                        data_val = np.array(df_prof.loc[:,variable].values)
                elif variable=='time':
                    data_val=df_prof.index.to_numpy()
                else: # Missing data
                    data_val = np.array([np.nan] * len(df_prof.index))
                
                self.data[variable]=data_val

            if not check_valid_profile(self.data["Press"], 3): # Check that pressure overcomes 3 dbar (i.e., profile deeper than 3 m)
                log("Invalid profile", indent=1,printlog=self.printlog)
                return False
            
            # Define top and bottom of the profile
            self.water_entry_index=np.where(self.data["Depth_KW"]>remove_topdist)[0][0] # Always take water entry index at certain distance below air pressure to remove the upper surface layer
            
            if np.argmax(self.data["Press"])>0:
                self.bottom_of_profile_index = np.where(self.data["Press"][0:np.argmax(self.data["Press"])]<=np.max(self.data["Press"])-remove_botdist)[0][-1]
            else: 
                log('Sinking part of the profile is missing', indent=1,printlog=self.printlog)
                return False
            
            # Compute air pressure
            if np.isnan(press_to_depth_factor):
                self.air_press=np.nan
            else:
                self.air_press=np.nanmean(self.data["Press"]-self.data["Depth_KW"]*press_to_depth_factor)

            return True
        except Exception:
            log("Failed to parse raw data from profile {}".format(kprof), indent=1,printlog=self.printlog)
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
            #df1['seconds_since_1970'] = list(pd.to_datetime(df1["Date1"], format= "%Y/%m/%d", dayfirst=True).values.astype(float) / 10 ** 9)
            df1['seconds_since_1970'] = list(pd.to_datetime(df1["Date1"],format= 'ISO8601', dayfirst=True).values.astype(float) / 10 ** 9) # Specify ISO8601 to deal with formats "yyyy/mm/dd HH:MM"
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
                    log("Latitude and longitude fall outside lake bounds.",printlog=self.printlog)
            else: # SBE files
                self.general_attributes["distance_to_GEF"] = np.nan
                self.general_attributes["latitude"] = np.nan
                self.general_attributes["longitude"] = np.nan
                
                
    def extract_profile(self, remove_botdist=1,remove_topdist=1,press_surface=100,):
        log("Extracting profile...", indent=1,printlog=self.printlog)
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
            diff_surface=diff_surface[(self.data["Press"][:np.argmax(self.data["Press"])]-np.nanmin(self.data["Press"]))<press_surface]    
            perc_cond = np.where(diff_cond > np.percentile(diff_surface, 99))
            #perc_cond_begin = np.where(diff_cond[:max_start] > np.percentile(diff_cond, 95))

            # if len(perc_cond_begin[0]) > 0:# Increase of conductivity occurs before max_start (then take last conductivity increase before max_start)
            #     water_entry_index = perc_cond_begin[0][-1] + 1
            # else:
            #     water_entry_index = perc_cond[0][0]
            press_first_peak=self.data["Press"][perc_cond[0][0]]-np.nanmin(self.data["Press"])
            press_last_peak=self.data["Press"][perc_cond[0][-1]]-np.nanmin(self.data["Press"])
            if perc_cond[0][0]>=1 and press_first_peak<0.5: # First conductivity peak is near the surface
                #self.air_press = np.percentile(self.data["Press"][:perc_cond[0][0]+1],0.05)
                self.air_press = np.nanmean(self.data["Press"][:perc_cond[0][0]+1])
                self.air_meas=True
                self.cond_peak_first=True
            elif perc_cond[0][-1]<len(self.data["Press"])-1 and perc_cond[0][-1]>np.argmax(self.data["Press"]) and press_last_peak<0.5: # Last conductivity peak is near the surface
                #self.air_press = np.percentile(self.data["Press"][perc_cond[0][-1]:],0.05)
                self.air_press = np.nanmean(self.data["Press"][perc_cond[0][-1]:])
                self.air_meas=True
                self.cond_peak_last=True
            elif perc_cond[0][0]==0 or perc_cond[0][-1]==len(self.data["Press"])-1: # No data point in the air
                #breakpoint()
                log('No data point above conductivity peak',indent=1,printlog=self.printlog)
                if perc_cond[0][0]==0:
                    self.air_press = np.nanmean(self.data["Press"][:2]) # Mean of the two first values
                    self.cond_peak_first=True
                elif perc_cond[0][-1]==len(self.data["Press"])-1:
                    self.air_press = np.nanmean(self.data["Press"][-2:]) # Mean of the two last values
                    self.cond_peak_last=True
                else:
                    return False
            else: #There is no conductivity peak
                log("No conductivity peak detected (first peak: "+str(press_first_peak)+" dbar, last peak: "+str(press_last_peak)+" dbar)", indent=1,printlog=self.printlog)    
                self.air_press =np.nanmin(self.data["Press"])
            
            if self.air_press-np.nanmin(self.data["Press"])>0.5:
                log("Issue in air pressure calculation", indent=1,printlog=self.printlog)
                return False
            
            water_entry_index=np.where(self.data["Press"]>self.air_press+remove_topdist)[0][0] # Always take water entry index at certain distance below air pressure to remove the upper layer
            
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
        self.bottom_of_profile_index = np.where(self.data["Press"][0:np.argmax(self.data["Press"])]<=np.max(self.data["Press"])-remove_botdist)[0][-1]
        #self.bottom_of_profile_index = np.argmax(self.data["Press"]) - remove_timesteps
        
        # if self.water_entry_index > 0:
        #     self.air_press = np.nanmean(self.data["Press"][0:self.water_entry_index])
        # else:
        #     self.air_press = np.nanmin(self.data["Press"][:self.bottom_of_profile_index])

        #self.air_press = np.nanmin(self.data["Press"][:self.bottom_of_profile_index]) # Always take the minimum pressure as the air pressure
        #self.air_press = np.percentile(self.data["Press"][0:max_start],0.05)
        return True

    def quality_assurance(self, file_path, simple=True,):
        log("Applying quality assurance", indent=1,printlog=self.printlog)
        quality_assurance_dict = json_converter(json.load(open(file_path)))
        try:
            for key, values in self.variables.copy().items():
                if ("_qual" not in key)and(key in quality_assurance_dict)and(sum(~np.isnan(self.data[key]))>0): # Not all the data is nan
                    if (quality_assurance_dict[key]["advanced"]) or (quality_assurance_dict[key]["simple"]):
                        name = key + "_qual"
                        self.variables[name] = {'var_name': name, 'dim': values["dim"],
                                                'unit': '0 = nothing to report, 1 = more investigation',
                                                'longname': name, }
                        if simple: #Always used
                            self.data[name] = qualityassurance(np.array(self.data[key]), np.array(self.data["time"]), **quality_assurance_dict[key]["simple"])
                            if "std_moving" in quality_assurance_dict[key].keys(): # Outlier removal based on std and moving average      
                                param_outliers=quality_assurance_dict[key]["std_moving"]
                                qa_bool=qa_std_moving(np.array(self.data[key]), np.array(self.data["Press"]), window_size=param_outliers["window_size"], factor=param_outliers["factor"], prior_flags=self.data[name].astype(bool))
                                self.data[name]=qa_bool.astype(int)
                        else:
                            quality_assurance_all = dict(quality_assurance_dict[key]["simple"], **quality_assurance_dict[key]["advanced"])
                            self.data[name] = qualityassurance(np.array(self.data[key]), np.array(self.data["time"]), **quality_assurance_all)
                        if key != "time":
                            self.data[name] = self.quality_assurance_ctd(self.data[name])
        except:
            breakpoint()

    def quality_assurance_ctd(self, qa): # To remove data before water entry and after reaching the bottom
        #qa: quality assurance values (0 or 1)
        if self.bottom_of_profile_index: 
            qa[self.bottom_of_profile_index:] = 1

        if self.water_entry_index:
            qa[:self.water_entry_index] = 1

        return qa

    def to_csv(self, folder, title,time_label="time",dimrows="depth_interp",grid=False,format_export="%.4f",var_to_remove=None):
        """
        Export profiles to csv file (only works for single profiles). 

        """
        
        log("Saving to csv file", indent=1,printlog=self.printlog)
        
        if var_to_remove!=None: # Some variables must be removed: include also the _qual ones
            for varname in var_to_remove:
                var_to_remove=var_to_remove+[varname+"_qual"]
        
        if grid: # Depth-interpolated data (Level 2B)
            variables = self.grid_variables
            dimensions = self.grid_dimensions
            data = self.grid
        else:
            variables = self.variables
            dimensions = self.dimensions
            data = self.data
        
        df=pd.DataFrame()
        
        
        datetime_val=[datetime.fromtimestamp(tnum,UTC) for tnum in data[time_label]]
        if not grid:
            df["Datetime [yyyymmddHHMMSS]"]=[int(dt.strftime('%Y%m%d%H%M%S')) for dt in datetime_val]
        for varname in variables:
            if (dimrows in variables[varname]["dim"]) and (var_to_remove==None or varname not in var_to_remove):
                if np.sum(~np.isnan(data[varname]))>0: # At least one non Nan value
                    if len(variables[varname]["dim"])==1:
                            df[varname+" ["+variables[varname]["unit"]+"]"]=data[varname]
                    elif len(variables[varname]["dim"])==2:
                        dimnames=np.array(variables[varname]["dim"])
                        if len(data[dimnames[dimnames!=dimrows][0]])==1: # Other dimension has a length of 1
                            df[varname+" ["+variables[varname]["unit"]+"]"]=data[varname]          
        # Put the depth data first
        if grid and "depth_interp [m]" in df.columns:
            df=df[["depth_interp [m]"]+list(np.array(df.columns)[np.array(df.columns)!="depth_interp [m]"])]
        filename = "{}_{}.csv".format(title, datetime_val[0].strftime('%Y%m%d_%H%M%S'))
        out_file = os.path.join(folder, filename)
        
        df.to_csv(out_file, sep=",",header=True,index=False,float_format=format_export)
        
    def var_to_csv(self, folder, title,var_to_export,time_label="time",dimrows="depth_interp",format_export="%.4f"):
        """
        Export a gridded variable (L3) to a csv file. 

        """
        
        log("Saving to csv file", indent=1,printlog=self.printlog)
        
        if not os.path.exists(folder): # Create folder if it doesn't exist
            os.makedirs(folder)

        variables = self.comb_variables
        dimensions = self.grid_dimensions
        data = self.grid

        datetime_val=[datetime.fromtimestamp(tnum,UTC) for tnum in data[time_label]]
        
        for varname in var_to_export:
            unit_var=variables[varname]["unit"].replace('/','_')
            print("Exporting {}_{}_{}.csv...".format(title, varname,unit_var))
            if variables[varname]["dim"]==(dimrows, time_label) and np.sum(~np.isnan(data[varname]))>0: # At least one non Nan value
                df=pd.DataFrame(data[varname],columns=datetime_val,index=data[dimrows])
            else:
                raise Exception("The selected variable cannot be exported to csv")
    
            filename = "{}_{}_{}.csv".format(title, varname,unit_var)
            out_file = os.path.join(folder, filename)
            if os.path.exists(out_file): # File already exist: delete it
                os.remove(out_file)
            
            # df.to_csv(out_file, sep=",",header=True,index=True,float_format=format_export)
            chunck_size=100
            for i in range(0, df.shape[0], chunck_size): # Export by subparts to make it faster
                df.iloc[i:i+chunck_size].to_csv(out_file, sep=",",mode='a', header=(i == 0), index=True,float_format=format_export)
        
        
    def to_netcdf(self, folder, title,  output_period="profile", mode='a', time_label="time", grid=False,):
        """
        Export profiles to netCDF files, either single profiles or depth-interpolated profiles.
        Inputs:
            folder: output folder
            title: title of the output files
            output_period: "weekly", "monthly", "yearly", "profile"
            mode: 'a' to append to existing files, 'w' to overwrite
            time_label: name of the time variable
            grid: True for depth-interpolated data (Level 2B), False for raw
            data (Level 2A).
        Outputs: 
            success_export: True if at least one profile was exported, False otherwise.
        """
        log("Saving to NetCDF", indent=1,printlog=self.printlog)

        success_export=False
        if not os.path.exists(folder): # Create folder if it doesn't exist
            os.makedirs(folder)

        if grid: # Depth-interpolated data (Level 2B)
            variables = self.grid_variables
            dimensions = self.grid_dimensions
            data = self.grid
        else:
            variables = self.variables
            dimensions = self.dimensions
            data = self.data
        time_arr = data[time_label] # Time values of the profile for L2A, only one value for L2B
        dt_min = datetime.fromtimestamp(np.nanmin(time_arr),UTC) # First time value of the profile
        dt_max = datetime.fromtimestamp(np.nanmax(time_arr),UTC) # Last time value of the profile
        
        if dt_max==dt_min: # Only one time value
            dt_max+=timedelta(seconds=1)
        
    
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
            log("Output periods {} not defined.".format(output_period),printlog=self.printlog)
            return
            
        while start < dt_max: 
            end = start + td
            s = datetime.timestamp(start)
            e = datetime.timestamp(end)

            filename = "{}_{}.nc".format(title, start.strftime('%Y%m%d_%H%M%S'))
            if grid:
                self.L2B_filename=filename
            out_file = os.path.join(folder, filename)
            log("Writing {} data from {} until {} to NetCDF file {}".format(title, start, end, filename), indent=1,printlog=self.printlog)
            if os.path.isfile(out_file): # File has already been created
                nc = netCDF4.Dataset(out_file, mode=mode, format='NETCDF4')
                nc_time = nc.variables[time_label]

                if time_arr[0] in nc_time: # Profile is already present in the netCDF file
                    log("Duplicated run, no data added", indent=2,printlog=self.printlog)
                    print("Profile already present, nc file not modified.")
                    nc.close()
                    start = start + td # Move to next time step (which will exit the function since new start > dt_max)
                    continue
                else:
                    idx = position_in_array(nc_time, time_arr[0]) # Where to insert the new profile
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
                    success_export=True

            else:
                
                nc = netCDF4.Dataset(out_file, mode='w', format='NETCDF4')

                for key in self.general_attributes:
                    setattr(nc, key, self.general_attributes[key])

                for key, values in dimensions.items():
                    # nc.createDimension(values['dim_name'], values['dim_size'])
                    if key !="time":
                        nc.createDimension(values['dim_name'], len(data[key]))
                    else: # Need to set time sze to None in order to increase it at each iteration
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
                success_export=True

            start = start + td
        return success_export
        
    def to_netcdf_combine(self, folder, title, mode='a', time_label="time",):
        """
        Export combined profiles to netCDF files (Level 3). 
        Inputs:
            folder: output folder
            title: title of the output files
            mode: 'a' to append to existing files, 'w' to overwrite
            time_label: name of the time variable
        Outputs: 
            success_export: True if at least one profile was exported, False otherwise.
        """
        log("Saving to combined NetCDF", indent=1,printlog=self.printlog)
        
        success_export=False
        if not os.path.exists(folder): # Create folder if it doesn't exist
            os.makedirs(folder)
        
        variables = self.comb_variables
        dimensions = self.grid_dimensions
        data = self.grid
        data["datetime"]=np.array([int(datetime.timestamp(data["time"][0],UTC).strftime('%Y%m%d%H%M%S'))])
        
        # Add min depth and max depth:
        data["min_depth"]=np.array([data["depth_interp"][np.where(~np.isnan(data["rho"]))[0][0]]])
        data["max_depth"]=np.array([data["depth_interp"][np.where(~np.isnan(data["rho"]))[0][-1]]])

        time_arr = data[time_label]

        filename = "{}.nc".format(title)
        out_file = os.path.join(folder, filename)
        log("Writing {} data to NetCDF file {}".format(title, filename), indent=1,printlog=self.printlog)
        if os.path.isfile(out_file): # File has already been created
            nc = netCDF4.Dataset(out_file, mode=mode, format='NETCDF4')
            nc_time = nc.variables[time_label]

            if time_arr[0] in nc_time: # Profile is already present in the netCDF file
                log("Duplicated run, no data added", indent=2,printlog=self.printlog)
                nc.close()
            else:
                idx = position_in_array(nc_time, time_arr[0]) # Where to insert the new profile
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
                success_export=True

        else:
            
            nc = netCDF4.Dataset(out_file, mode='w', format='NETCDF4')

            for key in self.general_attributes:
                setattr(nc, key, self.general_attributes[key])

            for key, values in dimensions.items():
                # nc.createDimension(values['dim_name'], values['dim_size'])
                if key !="time":
                    nc.createDimension(values['dim_name'], len(data[key]))
                else: # Need to set time size to None in order to increase it at each iteration
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
            success_export=True
        return success_export

    def write_to_L3(self,nc,time_label="time",newfile=True):
        variables = self.comb_variables
        dimensions = self.grid_dimensions
        data = self.grid

        time_arr = data[time_label]
        
        if not newfile: # File has already been created
            nc_time = nc.variables[time_label]

            if time_arr[0] in nc_time: # Profile is already present in the netCDF file
                log("Duplicated run, no data added", indent=2,printlog=self.printlog)
            else:
                idx = position_in_array(nc_time, time_arr[0]) # Where to insert the new profile
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

        else: # New file

            for key in self.general_attributes:
                setattr(nc, key, self.general_attributes[key])

            for key, values in dimensions.items():
                # nc.createDimension(values['dim_name'], values['dim_size'])
                if key !="time":
                    nc.createDimension(values['dim_name'], len(data[key]))
                else: # Need to set time size to None in order to increase it at each iteration
                    nc.createDimension(values['dim_name'], values['dim_size'])


            for key, values in variables.items(): 
                var = nc.createVariable(values["var_name"], np.float64, values["dim"], fill_value=np.nan)
                var.units = values["unit"]
                var.long_name = values["longname"]
                try:
                    #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                    if isinstance(data[key], str) and data[key]=='N/a':     
                        data[key]=np.nan
                    var[:]=data[key]
                    # if len(values["dim"]) == 1:
                    #     var[:] = data[key]
                    # elif len(values["dim"]) == 2:
                    #     var[:, 0] = data[key]
                    
                except:
                    breakpoint()
                    
    def add_to_dict(self,dict_name,time_label="time",newfile=True):
        """
        Add the data to a dictionary representing the netCDF file content.
        Returns True if data was added, False if data was already present.
        Inputs:
            dict_name: dictionary representing the netCDF file content.
            time_label: name of the time variable.
            newfile: boolean indicating if the file is new or not.
        Outputs:
            added_data: boolean indicating if data was added or not.
        """
        variables = self.comb_variables
        dimensions = self.grid_dimensions
        data = self.grid
        # data["datetime"]=np.array([int(datetime.utcfromtimestamp(data["time"][0]).strftime('%Y%m%d%H%M%S'))])
        
        # # Add min depth and max depth:
        # data["min_depth"]=np.array([data["depth_interp"][np.where(~np.isnan(data["rho"]))[0][0]]])
        # data["max_depth"]=np.array([data["depth_interp"][np.where(~np.isnan(data["rho"]))[0][-1]]])

        time_arr = data[time_label]
        added_data=True
        if not newfile: # File has already been created
            dict_time = dict_name[time_label]

            if time_arr[0] in dict_time: # Profile is already present in the netCDF file
                print("Data already present in the L3 netCDF file")
                added_data=False
            else:
                idx = position_in_array(dict_time, time_arr[0]) # Where to insert the new profile
                dict_time = np.insert(dict_time, idx, time_arr[0])
                for key, values in variables.items():
                    if key not in dict_name.keys():
                        print('Variable {} does not exist in the netCDF file'.format(key))
                    else:
                        #if key not in dimensions and key != "depth": 
                        if key not in dimensions: 
                            var = dict_name[key]
                            # if title=="L2B":
                            #     print(key)
                            #     breakpoint()
                            try:
                                #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                                if isinstance(data[key], str) and data[key]=='N/a':      
                                    data[key]=np.nan
                            except:
                                breakpoint()
                            # try:
                            #     if len(var.shape)==1:
                            #         end=len(var[:]) - 1 # last index
                            #     else:
                            #         end = len(var[:][0]) - 1 # last index of the second dimension
                            # except:
                            #     print(var)
                            # if idx != end: # New profile was taken before the previous last profile --> needs to be inserted
                            #     if len(var.shape)==1:
                            #         var[end] = data[key]
                            #         var[:] = var[np.insert(np.arange(end), idx, end)]
                            #     else:
                            #         var[:, end] = data[key]
                            #         var[:] = var[:, np.insert(np.arange(end), idx, end)]
                            # else:
                            #     if len(var.shape)==1:
                            #         var[idx] = data[key]
                            #     else:
                            #         var[:, idx] = data[key]
                            
                            if len(var.shape)==1:
                                var=np.insert(var,idx,data[key])
                            else:
                                var=np.insert(var,[idx],data[key],axis=1) # Insert a column
 
                            dict_name[key]=var
                dict_name[time_label]=dict_time

        else: # New file
            for key, values in variables.items(): 
                try:
                    #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                    if isinstance(data[key], str) and data[key]=='N/a':     
                        data[key]=np.nan
                    if len(values["dim"]) == 1:
                        dict_name[key] = data[key]
                    elif len(values["dim"]) == 2:
                        dict_name[key] = data[key]
                    
                except:
                    breakpoint()
        return added_data
    

    def profile_to_timeseries_grid(self, vars_nointerp,depthgrid=np.array([]),time_label="time",):
        log("Resampling profile to fixed grid...", indent=2,printlog=self.printlog)
        self.grid["depth_interp"] = self.fixed_depths_ref
        self.grid["time"] = [np.nanmin(self.data[time_label])]
        if ~np.any(depthgrid): # Use the level-corrected depth to interpolate
            depthgrid=self.data["depth_ref"]
            
        for key, values in self.grid_variables.items():
            if key not in self.grid_dimensions and key not in vars_nointerp: # Apply the interpolation for variables that are not dimensions and that are not listed in vars_nointerp
                
                mask = (~np.isnan(self.data[key])) & (~np.isnan(depthgrid))
                depths_ref = depthgrid[mask]
                data = self.data[key][mask]
                if len(data) < 50:
                    self.grid[key] = np.asarray([np.nan] * len(self.fixed_depths_ref))
                else:
                    self.grid[key] = np.interp(self.fixed_depths_ref, depths_ref, data, left=np.nan, right=np.nan)

    def derive_variables(self, lat, alt, df_gas,y_cond=0.874e-3, beta=0.807e-3,estimated_depth=False,):
        # Estimated_depth: must be a list
        if estimated_depth and np.isnan(self.air_press):
            calculate_depth=False
        else:
            calculate_depth=True
            
        log("Calculating derived variables...", indent=1,printlog=self.printlog)
        data = deepcopy(self.data)
        log("Masking variables for calculations", indent=1,printlog=self.printlog)
        for var in self.variables:
            if ("_qual" not in var) and (var+"_qual" in data.keys()): # Create mask on variables of "data"
                idx = data[var+"_qual"] > 0
                float_data = data[var].astype(float)
                float_data[idx] = np.nan
                data[var] = float_data.copy() # Corrected data (used to compute additional variables)
        if calculate_depth:
            data["adj_press"] = data["Press"] - self.air_press
        else:
            data["adj_press"]=np.array(estimated_depth)
        threshold = data["Temp"].shape[0] * 0.9
        if sum(np.isnan(data["Temp"])) > threshold or sum(np.isnan(data["Cond"])) > threshold or \
                sum(np.isnan(data["adj_press"])) > threshold:
            log("Not enough valid parameters for derived variables.", indent=2,printlog=self.printlog)
            breakpoint()
            return False
        else:
            self.variables.update(self.derived_variables)

        try:
            log("Calculating salinity...", indent=2,printlog=self.printlog)
            # self.data["SALIN"] = salinity(data["Temp"], data["Cond"], y_cond, temperature_func=default_salinity_temperature)
            self.data["SALIN"], self.data["Cond20"] = salinity_Kivu(data["Temp"], data["Cond"], temperature_func=fcond20_temperature_Kivu)
        except Exception:
            log("Failed to calculate salinity", indent=2,printlog=self.printlog)
            return False
        
        try:
            log("Calculating density...", indent=2,printlog=self.printlog)
            self.data["rho"] = np.asarray([1000] * len(data["Press"]))
            # rho_TS = density(temperature=data["Temp"], salinity=self.data["SALIN"],press=self.data["Press"])
            rho_TS = density_Kivu(temperature=data["Temp"], salinity=self.data["SALIN"],press=self.data["Press"])
            if calculate_depth: 
                # depth_TS=1e4 * data["adj_press"] / rho_TS / sw.g(lat)
                depth_TS=1e4 * data["adj_press"] / rho_TS / gsw.grav(lat, 0) # With gsw
            else:
                depth_TS=data["adj_press"]
            C_CH4=np.interp(depth_TS, df_gas["Depth"][~np.isnan(df_gas["CH4"])], df_gas["CH4"][~np.isnan(df_gas["CH4"])]*16/1000) # g/L
            C_CO2=np.interp(depth_TS, df_gas["Depth"][~np.isnan(df_gas["CO2"])], df_gas["CO2"][~np.isnan(df_gas["CO2"])]*44/1000) # g/L
            # self.data["rho"] = density(temperature=data["Temp"], salinity=self.data["SALIN"],C_CH4=C_CH4,C_CO2=C_CO2)
            self.data["rho"] = density_Kivu(temperature=data["Temp"], salinity=self.data["SALIN"],C_CH4=C_CH4,C_CO2=C_CO2)
        except Exception :
            log("Failed to calculate density", indent=2,printlog=self.printlog)
            return False

        log("Calculating depth...", indent=2,printlog=self.printlog)
        # rho_p=density(temperature=data["Temp"], salinity=self.data["SALIN"],press=data["adj_press"],C_CH4=C_CH4,C_CO2=C_CO2)
        rho_p=density_Kivu(temperature=data["Temp"], salinity=self.data["SALIN"],press=data["adj_press"],C_CH4=C_CH4,C_CO2=C_CO2)
        rho_avg=np.full(rho_p.shape,np.nan)
        ind0=np.where(~np.isnan(rho_p))[0][0] # First non NaN value
        
        # Method 1 (loop):
        # rho_avg[ind0:]=np.array([np.nanmean(rho_p[:i+1]) for i in range(ind0,len(rho_p))]) # Average density above depth of interest
        
        # Method 2 (loop and warning message):
        # rho_avg=np.array([np.nanmean(rho_p[:i+1]) for i in range(len(rho_p))])
        
        # Method 3 (no loop=faster)
        indrho=np.full((len(rho_p)-ind0,),1.0)
        indrho[np.isnan(rho_p[ind0:])]=np.nan
        rho_avg[ind0:]=np.nancumsum(rho_p[ind0:])/np.nancumsum(indrho)
    
        if calculate_depth:  
            #self.data["depth"] = 1e4 * data["adj_press"] / (rho_avg*sw.g(lat))
            self.data["depth"] = 1e4 * data["adj_press"] / (rho_avg*gsw.grav(lat, 0)) # With gsw
        else:
            self.data["depth"]=data["adj_press"]
        log("Calculating depth_ref...", indent=2,printlog=self.printlog)
        self.data["depth_ref"] = self.data["depth"] + self.depth_value
        b=(self.data["depth_ref"])
        try:
            log("Calculating potential temperature...", indent=2,printlog=self.printlog)
            self.data["pt"]  = potential_temperature_gsw(S=self.data["SALIN"], T=data["Temp"], p=data["adj_press"], p_ref=0)
        except Exception:
            self.data["pt"] = np.asarray([np.nan] * len(data["time"]))
            log("Failed to calculate potential temperature",printlog=self.printlog)

        try:
            log("Calculating potential density...", indent=2,printlog=self.printlog)
            # self.data["prho"] = density(self.data["pt"], self.data["SALIN"])
            self.data["prho"] = density_Kivu(self.data["pt"], self.data["SALIN"])
        except Exception:
            log("Failed to calculate potential density", indent=2,printlog=self.printlog)

        try:
            log("Calculating oxygen saturation...", indent=2,printlog=self.printlog)
            conc_sat = oxygen_saturation(self.data["pt"], self.data["SALIN"], alt, lat) # Saturation concentration [mg/L]
            self.data["sat"] = self.data["DO_mg"]/conc_sat*100 # [%sat]
            
        except Exception :
            log("Failed to replace oxygen saturation", indent=2,printlog=self.printlog)

        try:
            log("Calculating Thorpe Dispacements...", indent=2,printlog=self.printlog)
            sorted_pt = np.argsort(self.data["pt"])[::-1]
            self.data["thorpe"] = -(self.data["depth"] - self.data["depth"][sorted_pt]) 
        except Exception :
            log("Failed to calculate Thorpe Displacements", indent=2,printlog=self.printlog)

        return True
        
    def mask_data(self):
        for var in self.variables:
            if ("_qual" not in var) and (var+"_qual" in self.variables):
                idx = self.data[var+"_qual"] > 0
                if sum(idx)>0: # At least one value to remove
                    self.data[var][idx] = np.nan               

    def read_processed_data(self, file):
        self.data = netCDF4.Dataset(file, 'r').variables
        for key in self.data.keys():
            self.data[key] = self.data[key][:]
