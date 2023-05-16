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
import collections
import pylake
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *
    
class ctd_database:
    def __init__(self):
        self.general_attributes = {
            "institution": "Eawag",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "title": "Lake Kivu database",
            "comment": "Database computed from CTD profiles in Lake Kivu ",
        }

        self.dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            "depth_interp": {'dim_name': "depth_interp", 'dim_size': None}
        }

        
        self.variables = {
            'data_type': {'var_name': 'data_type', 'dim': ('time',), 'unit': '-', 'longname': 'Data type: 0 (government) or 1 (KW)'},
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'time'},
            'datetime': {'var_name': 'datetime', 'dim': ('time',), 'unit': '-', 'longname': 'Date and time as integer yyyymmddHHMMSS'},
            'min_depth': {'var_name': 'min_depth', 'dim': ('time',), 'unit': 'm', 'longname': 'Minimum depth'},
            'max_depth': {'var_name': 'max_depth', 'dim': ('time',), 'unit': 'm', 'longname': 'Maximum depth'},
            'Press': {'var_name':'Press', 'dim':('depth_interp','time'), 'unit': 'dbar', 'longname': 'pressure'},
            "depth_interp": {'var_name': "depth_interp", 'dim': ('depth_interp',), 'unit': 'm', 'longname': "Interpolated depth"},
            'Temp': {'var_name': 'Temp', 'dim': ('depth_interp', 'time'), 'unit': 'degC', 'longname': 'temperature'},
            'Cond': {'var_name': 'Cond', 'dim': ('depth_interp', 'time'), 'unit': 'mS/cm', 'longname': 'conductivity'},
            "SALIN": {'var_name': 'SALIN', 'dim': ('depth_interp', 'time'), 'unit': 'PSU', 'longname': 'salinity'},
            'Turb': {'var_name': 'Turb', 'dim': ('depth_interp', 'time'), 'unit': 'FTU', 'longname': 'Turbidity'},
            'pH': {'var_name': 'pH', 'dim': ('depth_interp', 'time'), 'unit': '_', 'longname': 'pH'},
            "rho": {'var_name': "rho", 'dim': ('depth_interp', 'time'), 'unit': 'kg/m3', 'longname': "Density", },           
            "latitude": {'var_name': 'latitude', 'dim': ('time',), 'unit': '°', 'longname': 'latitude'},
            "longitude": {'var_name': 'longitude', 'dim': ('time',), 'unit': '°', 'longname': 'longitude'},
            "dist_GEF": {'var_name': 'dist_GEF', 'dim': ('time',), 'unit': 'm', 'longname': 'Distance to closest methane extraction plant'},
            "z_maxdens": {'var_name': 'z_maxdens', 'dim': ('time',), 'unit': 'm', 'longname': 'Depth of maxmimum density gradient'},
            "z_therm": {'var_name': 'z_therm', 'dim': ('time',), 'unit': 'm', 'longname': 'Thermocline depth'},
            "Sc": {'var_name': 'Sc', 'dim': ('time',), 'unit': 'J.m-2', 'longname': 'Schmidt stability'},
            "trendprof_Temp": {'var_name': 'trendprof_Tem', 'dim': ('depth_interp', 'time'), 'unit': 'degC/yr', 'longname': 'Temnperature trends with respect to reference period'},
            "trendprof_Cond": {'var_name': 'trendprof_Cond', 'dim': ('depth_interp', 'time'), 'unit': 'mS/cm/yr', 'longname': 'Conductivity dtrends with respect to reference period'},
            "trendprof_rho": {'var_name': 'trendprof_rho', 'dim': ('depth_interp', 'time'), 'unit': 'kg/m3/yr', 'longname': 'Density trends with respect to reference period'},
        }
        
        self.data = {}

    def compute_maxdens(self):
        # Maximum density gradient
        grad_rho=np.abs(np.gradient(self.data["rho"], axis=0))
        self.data["z_maxdens"]=self.data["depth_interp"][np.nanargmax(grad_rho,axis=0)]
        
    def compute_stratification_pylake(self,lat,deptha,area):
        z_therm=np.full(len(self.data["time"]),np.nan)
        Sc=np.full(len(self.data["time"]),np.nan)
        for kt in np.arange(len(self.data["time"])):
            print('Progress: {:.2f} %'.format(kt/len(self.data["time"])*100))
            valkeep=~np.isnan(self.data["Temp"][:,kt])
            # Seasonal thermocline using density computed from temperature and salinity (not ideal)
            z_therm[kt],_=pylake.seasonal_thermocline(self.data["Temp"][valkeep,kt], 
                                                      depth=self.data["depth_interp"][valkeep], s=self.data["SALIN"][valkeep,kt])
            # Schmidt stability
            Sc[kt]=pylake.schmidt_stability(self.data["Temp"][valkeep,kt], depth=self.data["depth_interp"][valkeep], 
                                            bthA=area, bthD=deptha, sal = self.data["SALIN"][valkeep,kt], g=sw.g(lat))
        self.data["z_therm"]=z_therm
        self.data["Sc"]=Sc

        
    def to_netcdf(self, filename, mode='a', time_label="time",):
        log("Saving to NetCDF", indent=1)
    
        variables = self.variables
        dimensions = self.dimensions
        data = self.data

        log("Writing data to NetCDF file {}".format(filename), indent=1)
 
        nc = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

        for key in self.general_attributes:
            setattr(nc, key, self.general_attributes[key])

        for key, values in dimensions.items():
            nc.createDimension(values['dim_name'], values['dim_size'])

        for key, values in variables.items():
            var = nc.createVariable(values["var_name"], np.float64, values["dim"], fill_value=np.nan)
            var.units = values["unit"]
            var.long_name = values["longname"]
            try:
                if (key not in data.keys()) or (isinstance(data[key], str) and data[key]=='N/a'): # No data
                    if len(values["dim"])==1:
                        data[key]=np.full(len(data[values["dim"][0]]),np.nan)
                    else:
                        data[key]=np.full((len(data[values["dim"][0]]),len(data[values["dim"][1]])),np.nan)
                
                    data[key]=np.nan 
                var[:] = data[key]

            except:
                breakpoint()
                nc.close()
        nc.close()
        log("netCDF file created!", indent=1)
            
class ctd_periods:
    def __init__(self):
        self.general_attributes = {
            "institution": "Eawag",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "title": "Lake Kivu database organized in periods",
            "comment": "Variables computed for three periods: reference, p1 before extraction, p2 after extraction",
        }
    
        self.dimensions = {
            'time0_periods': {'dim_name': 'time0_periods', 'dim_size': None},
            "depth_interp": {'dim_name': "depth_interp", 'dim_size': None}
        }
    
        
        self.variables = {
            'time0_periods': {'var_name': 'time0_periods', 'dim': ('time0_periods',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'Starting time of periods'},
            'timef_periods': {'var_name': 'timef_periods', 'dim': ('time0_periods',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'Ending time of periods'},
            "depth_interp": {'var_name': "depth_interp", 'dim': ('depth_interp',), 'unit': 'm', 'longname': "Interpolated depth"},
            
            "meanprof_Temp_avg":{'var_name': "meanprof_Temp_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'degC', 'longname': "Mean temperature profile"},
            "meanprof_Temp_std":{'var_name': "meanprof_Temp_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'degC', 'longname': "Profile of temperature std"},        
            "meantrendprof_Temp_avg":{'var_name': "meantrendprof_Temp_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'degC/yr', 'longname': "Mean profile of temperature trend"},
            "meantrendprof_Temp_std":{'var_name': "meantrendprof_Temp_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'degC/yr', 'longname': "Std profile of temperature trend"},
            
            "meanprof_Cond_avg":{'var_name': "meanprof_Cond_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm', 'longname': "Mean conductivity profile"},
            "meanprof_Cond_std":{'var_name': "meanprof_Cond_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm', 'longname': "Profile of conductivity std"}, 
            "meantrendprof_Cond_avg":{'var_name': "meantrendprof_Cond_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm/yr', 'longname': "Mean profile of conductivity trend"},
            "meantrendprof_Cond_std":{'var_name': "meantrendprof_Cond_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm/yr', 'longname': "Std profile of conductivity trend"},
            
            "meanprof_rho_avg":{'var_name': "meanprof_rho_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3', 'longname': "Mean density profile"},
            "meanprof_rho_std":{'var_name': "meanprof_rho_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3', 'longname': "Profile of density std"},  
            "meantrendprof_rho_avg":{'var_name': "meantrendprof_rho_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3/yr', 'longname': "Mean profile of density trend"},
            "meantrendprof_rho_std":{'var_name': "meantrendprof_rho_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3/yr', 'longname': "Std profile of density trend"},    
        }
        
        self.data = {}
        
        
    def compute_trends(self,database,period_ref=[datetime(2008,1,1),datetime(2011,1,1)],date_extraction=datetime(2016,1,1)):
        # Average reference profile
        self.data["depth_interp"]=database.data["depth_interp"]
        
        tperiod_ref=[period_ref[k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
        textraction=date_extraction.replace(tzinfo=timezone.utc).timestamp()
        self.data["time0_periods"]=np.array([tperiod_ref[0],tperiod_ref[1],textraction])
        self.data["timef_periods"]=np.array([tperiod_ref[1],textraction,np.max(database.data["time"])])
        indprof_ref=np.where(np.logical_and(database.data["time"]>tperiod_ref[0],database.data["time"]<tperiod_ref[1]))[0]
        indprof_p1=np.where(np.logical_and(database.data["time"]>tperiod_ref[1],database.data["time"]<textraction))[0]
        indprof_p2=np.where(database.data["time"]>=textraction)[0]
        prof_avg=dict()
        prof_trend=dict()
        prof_trendavg=dict()
        
        for var in ["Temp","Cond","rho"]:
            prof_avg[var+"_ref"]=np.nanmean(database.data[var][:,indprof_ref],axis=1)
            prof_avg[var+"_ref_std"]=np.nanstd(database.data[var][:,indprof_ref],axis=1)
            prof_avg[var+"_p1"]=np.nanmean(database.data[var][:,indprof_p1],axis=1)
            prof_avg[var+"_p1_std"]=np.nanstd(database.data[var][:,indprof_p1],axis=1)
            prof_avg[var+"_p2"]=np.nanmean(database.data[var][:,indprof_p2],axis=1)
            prof_avg[var+"_p2_std"]=np.nanstd(database.data[var][:,indprof_p2],axis=1)
            refprof=prof_avg[var+"_ref"][:,np.newaxis]
            prof_trend[var]=(database.data[var]-refprof)/((database.data["time"]-np.mean(tperiod_ref))/(3600*24*365))
            # prof_trendavg[var+"_p1"]=np.nanmean(prof_trend[var][:,indprof_p1],axis=1)
            # prof_trendavg[var+"_p1_std"]=np.nanstd(prof_trend[var][:,indprof_p1],axis=1)
            # prof_trendavg[var+"_p2"]=np.nanmean(prof_trend[var][:,indprof_p2],axis=1)
            # prof_trendavg[var+"_p2_std"]=np.nanstd(prof_trend[var][:,indprof_p2],axis=1)
            
            
            trend_p1=(database.data[var][:,indprof_p1[1:]]-database.data[var][:,indprof_p1[0]][:,np.newaxis])/((database.data["time"][indprof_p1[1:]]-database.data["time"][indprof_p1[0]])/(3600*24*365))
            trend_p2=(database.data[var][:,indprof_p2[1:]]-database.data[var][:,indprof_p2[0]][:,np.newaxis])/((database.data["time"][indprof_p2[1:]]-database.data["time"][indprof_p2[0]])/(3600*24*365))
            prof_trendavg[var+"_p1"]=np.nanmean(trend_p1,axis=1)
            prof_trendavg[var+"_p1_std"]=np.nanstd(trend_p1,axis=1)
            prof_trendavg[var+"_p2"]=np.nanmean(trend_p2,axis=1)
            prof_trendavg[var+"_p2_std"]=np.nanstd(trend_p2,axis=1)
            
            self.data["meanprof_"+var+"_avg"]=np.concatenate((prof_avg[var+"_ref"][:,np.newaxis],prof_avg[var+"_p1"][:,np.newaxis],prof_avg[var+"_p2"][:,np.newaxis]),axis=1)
            self.data["meanprof_"+var+"_std"]=np.concatenate((prof_avg[var+"_ref_std"][:,np.newaxis],prof_avg[var+"_p1_std"][:,np.newaxis],prof_avg[var+"_p2_std"][:,np.newaxis]),axis=1)
            database.data["trendprof_"+var]=prof_trend[var]
            self.data["meantrendprof_"+var+"_avg"]=np.concatenate((np.zeros((len(database.data["depth_interp"]),1)),prof_trendavg[var+"_p1"][:,np.newaxis],prof_trendavg[var+"_p2"][:,np.newaxis]),axis=1)
            self.data["meantrendprof_"+var+"_std"]=np.concatenate((np.zeros((len(database.data["depth_interp"]),1)),prof_trendavg[var+"_p1_std"][:,np.newaxis],prof_trendavg[var+"_p2_std"][:,np.newaxis]),axis=1)
        
        return prof_avg, prof_trend,prof_trendavg
    
    def to_netcdf(self, filename, mode='a', time_label="time",):
        log("Saving to NetCDF", indent=1)
    
        variables = self.variables
        dimensions = self.dimensions
        data = self.data
    
        log("Writing data to NetCDF file {}".format(filename), indent=1)
     
        nc = netCDF4.Dataset(filename, mode='w', format='NETCDF4')
    
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