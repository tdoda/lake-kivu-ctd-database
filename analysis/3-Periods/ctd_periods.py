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
from scipy.optimize import curve_fit
import seawater as sw
import re as re
import collections
import pylake
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *
            
class ctd_periods:
    def __init__(self):
        self.general_attributes = {
            "institution": "Eawag",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "title": "Lake Kivu database organized in periods",
            "comment": "Variables averaged over periods (e.g., reference, p1 before extraction, p2 after extraction)",
        }
    
        self.dimensions = {
            'time': {'dim_name': 'time', 'dim_size': None},
            'time0_periods': {'dim_name': 'time0_periods', 'dim_size': None},
            "depth_interp": {'dim_name': "depth_interp", 'dim_size': None},
            "depth_trend": {'dim_name': "depth_trend", 'dim_size': None},
            "temp_trend": {'dim_name': "temp_trend", 'dim_size': None},
            "cond_trend": {'dim_name': "cond_trend", 'dim_size': None},
            "salin_trend": {'dim_name': "salin_trend", 'dim_size': None},
            "rho_trend": {'dim_name': "rho_trend", 'dim_size': None},
        }
    
        
        self.variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'Time of each profile'},
            'time0_periods': {'var_name': 'time0_periods', 'dim': ('time0_periods',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'Starting time of periods'},
            'timef_periods': {'var_name': 'timef_periods', 'dim': ('time0_periods',), 'unit': 'seconds since 1970-01-01 00:00:00', 'longname': 'Ending time of periods'},
            "depth_interp": {'var_name': "depth_interp", 'dim': ('depth_interp',), 'unit': 'm', 'longname': "Interpolated depth"},
            "depth_trend": {'var_name': "depth_trend", 'dim': ('depth_trend',), 'unit': 'm', 'longname': "Depth for trends"},
            
            "meanprof_Temp_avg":{'var_name': "meanprof_Temp_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'degC', 'longname': "Mean temperature profile"},
            "meanprof_Temp_std":{'var_name': "meanprof_Temp_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'degC', 'longname': "Profile of temperature std"},        
            "trendavg_Temp":{'var_name': "trendavg_Temp", 'dim': ('depth_trend','time0_periods'), 'unit': 'degC/yr', 'longname': "Average temperature trend"},
            "trendfit_Temp":{'var_name': "trendfit_Temp", 'dim': ('depth_trend','time0_periods'), 'unit': 'degC/yr', 'longname': "Temperature trend from linear fit"},
            "R2fit_Temp":{'var_name': "R2fit_Temp", 'dim': ('depth_trend','time0_periods'), 'unit': '-', 'longname': "Regression coefficient R2 of the temperature trend fit"},
            "interceptfit_Temp":{'var_name': "interceptfit_Temp", 'dim': ('depth_trend','time0_periods'), 'unit': 'degC', 'longname': "Intercept of the temperature fit"},
            "trenddata_Temp":{'var_name': "tenddata_Temp", 'dim': ('depth_trend','time'), 'unit': 'degC', 'longname': "Temperature data used to compute trends"},
            "temp_trend":{'var_name': "temp_trend", 'dim': ('temp_trend',), 'unit': '°C', 'longname': "Temperature values for isotherms displacements"},
            "z_iso_Temp":{'var_name': "z_iso_Temp", 'dim': ('temp_trend','time'), 'unit': 'm', 'longname': "Depth of isotherms"},
            "trendavg_iso_Temp":{'var_name': "trendavg_iso_Temp", 'dim': ('temp_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average isotherms displacements"},
            "trendfit_iso_Temp":{'var_name': "trendfit_iso_Temp", 'dim': ('temp_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Isotherms displacements from linear fit"},
            
            "meanprof_Cond_avg":{'var_name': "meanprof_Cond_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm', 'longname': "Mean conductivity profile"},
            "meanprof_Cond_std":{'var_name': "meanprof_Cond_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm', 'longname': "Profile of conductivity std"}, 
            "trendavg_Cond":{'var_name': "trendavg_Cond", 'dim': ('depth_trend','time0_periods'), 'unit': 'mS.cm-1.yr-1', 'longname': "Average conductivity trend"},
            "trendfit_Cond":{'var_name': "trendfit_Cond", 'dim': ('depth_trend','time0_periods'), 'unit': 'mS.cm-1.yr-1', 'longname': "Conductivity trend from linear fit"},
            "R2fit_Cond":{'var_name': "R2fit_Cond", 'dim': ('depth_trend','time0_periods'), 'unit': '-', 'longname': "Regression coefficient R2 of the conductivity trend fit"},
            "interceptfit_Cond":{'var_name': "interceptfit_Cond", 'dim': ('depth_trend','time0_periods'), 'unit': 'mS.cm-1', 'longname': "Intercept of the conductivity fit"},
            "trenddata_Cond":{'var_name': "trenddata_Cond", 'dim': ('depth_trend','time'), 'unit': 'mS.cm-1', 'longname': "Conductivity data used to compute trends"},
            "cond_trend":{'var_name': "cond_trend", 'dim': ('cond_trend',), 'unit': 'mS.cm-1', 'longname': "Conductivity values for isolines displacements"},
            "z_iso_Cond":{'var_name': "z_iso_Cond", 'dim': ('cond_trend','time'), 'unit': 'm', 'longname': "Depth of conductivity isolines"},
            "trendavg_iso_Cond":{'var_name': "trendavg_iso_Cond", 'dim': ('cond_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average conductivity isolines displacements"},
            "trendfit_iso_Cond":{'var_name': "trendfit_iso_Cond", 'dim': ('cond_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Conductivity isolines displacements from linear fit"},
                       
            "meanprof_SALIN_avg":{'var_name': "meanprof_SALIN_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'g/kg', 'longname': "Mean salinity profile"},
            "meanprof_SALIN_std":{'var_name': "meanprof_SALIN_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'g/kg', 'longname': "Profile of salinity std"}, 
            "trendavg_SALIN":{'var_name': "trendavg_SALIN", 'dim': ('depth_trend','time0_periods'), 'unit': 'g.kg-1.yr-1', 'longname': "Average salinity trend"},
            "trendfit_SALIN":{'var_name': "trendfit_SALIN", 'dim': ('depth_trend','time0_periods'), 'unit': 'g.kg-1.yr-1', 'longname': "Salinity trend from linear fit"},
            "R2fit_SALIN":{'var_name': "R2fit_SALIN", 'dim': ('depth_trend','time0_periods'), 'unit': '-', 'longname': "Regression coefficient R2 of the salinity trend fit"},
            "interceptfit_SALIN":{'var_name': "interceptfit_SALIN", 'dim': ('depth_trend','time0_periods'), 'unit': 'g/kg', 'longname': "Intercept of the salinity fit"},
            "trenddata_SALIN":{'var_name': "trenddata_SALIN", 'dim': ('depth_trend','time'), 'unit': 'g/kg', 'longname': "Salinity data used to compute trends"},
            "salin_trend":{'var_name': "salin_trend", 'dim': ('salin_trend',), 'unit': 'g/kg', 'longname': "Salinity values for isohalines displacements"},
            "z_iso_SALIN":{'var_name': "z_iso_SALIN", 'dim': ('salin_trend','time'), 'unit': 'm', 'longname': "Depth of isohalines"},
            "trendavg_iso_SALIN":{'var_name': "trendavg_iso_SALIN", 'dim': ('salin_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average isohalines displacements"},
            "trendfit_iso_SALIN":{'var_name': "trendfit_iso_SALIN", 'dim': ('salin_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Isohalines displacements from linear fit"},
                        
            "meanprof_rho_avg":{'var_name': "meanprof_rho_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3', 'longname': "Mean density profile"},
            "meanprof_rho_std":{'var_name': "meanprof_rho_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3', 'longname': "Profile of density std"},  
            "trendavg_rho":{'var_name': "trendavg_rho", 'dim': ('depth_trend','time0_periods'), 'unit': 'kg.m-3.yr-1', 'longname': "Average density trend"},
            "trendfit_rho":{'var_name': "trendfit_rho", 'dim': ('depth_trend','time0_periods'), 'unit': 'kg.m-3.yr-1', 'longname': "Density trend from linear fit"},
            "R2fit_rho":{'var_name': "R2fit_rho", 'dim': ('depth_trend','time0_periods'), 'unit': '-', 'longname': "Regression coefficient R2 of the density trend fit"},
            "interceptfit_rho":{'var_name': "interceptfit_rho", 'dim': ('depth_trend','time0_periods'), 'unit': 'kg.m-3', 'longname': "Intercept of the density fit"},
            "trenddata_rho":{'var_name': "trenddata_rho", 'dim': ('depth_trend','time'), 'unit': 'kg.m-3', 'longname': "Density data used to compute trends"},
            "rho_trend":{'var_name': "rho_trend", 'dim': ('rho_trend',), 'unit': 'kg.m-3', 'longname': "Density values for isopycnals displacements"},
            "z_iso_rho":{'var_name': "z_iso_rho", 'dim': ('rho_trend','time'), 'unit': 'm', 'longname': "Depth of isopycnals"},
            "trendavg_iso_rho":{'var_name': "trendavg_iso_rho", 'dim': ('rho_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average ispoyncals displacements"},
            "trendfit_iso_rho":{'var_name': "trendfit_iso_rho", 'dim': ('rho_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Ispoyncals displacements from linear fit"},
            
            "meanprof_N2_avg":{'var_name': "meanprof_N2_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 's-2', 'longname': "Mean squared buoyancy frequency"},
            "meanprof_N2_std":{'var_name': "meanprof_N2_std", 'dim': ('depth_interp','time0_periods'), 'unit': 's-2', 'longname': "Profile of squared buoyancy frequency std"}, 
            "trendavg_N2":{'var_name': "trendavg_N2", 'dim': ('depth_trend','time0_periods'), 'unit': 's-2.yr-1', 'longname': "Average N2 trend"},
            "trendfit_N2":{'var_name': "trendfit_N2", 'dim': ('depth_trend','time0_periods'), 'unit': 's-2.yr-1', 'longname': "N2 trend from linear fit"}, 
            "R2fit_N2":{'var_name': "R2fit_N2", 'dim': ('depth_trend','time0_periods'), 'unit': '-', 'longname': "Regression coefficient R2 of the N2 trend fit"},
            "interceptfit_N2":{'var_name': "interceptfit_N2", 'dim': ('depth_trend','time0_periods'), 'unit': 's-2', 'longname': "Intercept of the N2 fit"},
            "trenddata_N2":{'var_name': "trenddata_N2", 'dim': ('depth_trend','time'), 'unit': 's-2', 'longname': "N2 data used to compute trends"},
            
            "z_chem":{'var_name': "z_chem", 'dim': ('time0_periods',), 'unit': 'm', 'longname': "Chemocline depth from maximum density gradient"},
            }
        
        self.data = {}
        
    
    def compute_avgprof(self,database,t0_periods,tf_periods,varnames=["Temp","Cond","SALIN","rho"]):
        # t0_periods: initial time of each period
        # tf_periods: final time of each period
        
        
        # Convert datetime periods into timestamp:
        t0_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in t0_periods])
        tf_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in tf_periods])
        
        
        self.data["depth_interp"]=database["depth_interp"]
        self.data["time0_periods"]=t0_periods
        self.data["timef_periods"]=tf_periods
        
        prof_avg=dict()
        prof_std=dict()
        # trend_avg=dict()
        # trend_std=dict()
        # trend_fit=dict()
        
        for var in varnames:
            prof_avg[var]=np.full((len(self.data["depth_interp"]),len(t0_periods)),np.nan)
            prof_std[var]=np.full((len(self.data["depth_interp"]),len(t0_periods)),np.nan)
            # trend_avg[var]=np.full((len(self.data["depth_interp"]),len(t0_periods)),np.nan)
            # trend_std[var]=np.full((len(self.data["depth_interp"]),len(t0_periods)),np.nan)
            # trend_fit[var]=np.full((len(self.data["depth_interp"]),len(t0_periods)),np.nan)
            
            log('Calculation average prof for '+var,indent=1)
            for kp in range(len(t0_periods)):       
                indprof=np.where(np.logical_and(database["time"]>t0_periods[kp],database["time"]<tf_periods[kp]))[0]   
                prof_avg[var][:,kp]=np.nanmean(database[var][:,indprof],axis=1)
                prof_std[var][:,kp]=np.nanstd(database[var][:,indprof],axis=1)
                # trendval=np.diff(database[var][:,indprof],axis=1)/(np.diff(database['time'][indprof])/(3600*24*365)) # x/yr
                # trend_avg[var][:,kp]=np.nanmean(trendval,axis=1)
                # trend_std[var][:,kp]=np.nanstd(trendval,axis=1) 
                # trend_prof=np.full((len(database["depth_interp"]),),np.nan) # Profile of trends
                # for kz in range(len(database["depth_interp"])): 
                #     if sum(np.isnan(database[var][kz,indprof]))<len(indprof)-2: # At least 3 samples
                #         pfit,_,_=regression_oneline(database['time'][indprof]/(3600*24*365),database[var][kz,indprof])
                #         trend_prof[kz]=pfit[0]
                # trend_fit[var][:,kp]=trend_prof
                
            self.data["meanprof_"+var+"_avg"]=prof_avg[var]
            self.data["meanprof_"+var+"_std"]=prof_std[var]
            
        return prof_avg, prof_std
    
    
    
    def compute_avgtrend(self,database,t0_periods,tf_periods,dz,dvar=[0.001,0.001,0.001,0.001],varnames=["Temp","Cond","SALIN","rho"],nmin=10,mindur=1):
        # t0_periods: initial time of each period
        # tf_periods: final time of each period
        # dz: new depth step to compute trend
        # dvar: step for trends of isolines (for each variable)
        # varnames: variable names
        # nmin: minimum number of values needed to ompute trend
        # mindur [yr]: minimum duration spanned by the data to calculate trend 
        
        
        # Convert datetime periods into timestamp:
        t0_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in t0_periods])
        tf_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in tf_periods])
        
        depth_trend=np.arange(self.data["depth_interp"][0],self.data["depth_interp"][-1],dz)
        # temp_trend=np.arange(round(np.nanmin(database["Temp"])/dT)*dT,round(np.nanmax(database["Temp"])/dT)*dT,dT)
        # cond_trend=np.arange(round(np.nanmin(database["Cond"])/dC)*dC,round(np.nanmax(database["Cond"])/dC)*dC,dC)
        # salin_trend=np.arange(round(np.nanmin(database["SALIN"])/dS)*dS,round(np.nanmax(database["SALIN"])/dS)*dS,dS)
        # rho_trend=np.arange(round(np.nanmin(database["rho"])/drho)*drho,round(np.nanmax(database["rho"])/drho)*drho,drho)
        
        self.data["depth_trend"]=depth_trend
        self.data["time"]=database["time"]
        if "time0_periods" not in self.data.keys():
            self.data["time0_periods"]=t0_periods
            self.data["timef_periods"]=tf_periods
        
        
        trend_avg=dict()
        trend_fit=dict()
        R2_fit=dict()
        trend_iso_avg=dict()
        trend_iso_fit=dict()
        intercept_fit=dict()
        
        
        
        kvar=-1
        z_iso_all=dict()
        for var in varnames:
            kvar+=1
            nlayers=round((self.data["depth_interp"][-1]-self.data["depth_interp"][0])/dz)
            nval=round(dz/(self.data["depth_interp"][1]-self.data["depth_interp"][0]))
            prof_avg=np.mean(database[var].reshape((nval,-1),order='F'),axis=0).reshape((nlayers,-1),order='F') # Profile with new z resolution(depth_trend), averages in each layer 
            trend_avg[var]=np.full((len(depth_trend),len(t0_periods)),np.nan)
            trend_fit[var]=np.full((len(depth_trend),len(t0_periods)),np.nan)
            R2_fit[var]=np.full((len(depth_trend),len(t0_periods)),np.nan)
            intercept_fit[var]=np.full((len(depth_trend),len(t0_periods)),np.nan)
            
            # Create matrix with isolines positions
            # var_trend=np.arange(round(np.nanmin(database[var])/dvar[kvar])*dvar[kvar],round(np.nanmax(database[var])/dvar[kvar])*dvar[kvar],dvar[kvar])
            # self.data[var.lower()+"_trend"]=var_trend
            # z_iso=np.full((len(var_trend),len(database["time"])),np.nan)
            # data_smooth=movmean(database[var],10,axis=1) # Temporal smoothening
            # for kp in range(len(database["time"])):
            #     # Get location of isolines: could be problematic when non monotic changes in the data (several locations for the same isoline)
            #     # Do not consider the upper 100 m for temperature because decreasing T with depth
            #     data_prof=data_smooth[:,kp]
            #     if var=="Temp":
            #         data_prof[database["depth_interp"]<100]=np.nan
            #     indsort=np.argsort(data_prof) # Sort values
            #     z_iso[:,kp]=np.interp(var_trend,data_prof[indsort],database["depth_interp"][indsort],left=np.nan,right=np.nan) 
            
            # z_iso_all[var]=z_iso
            # trend_iso_avg[var]=np.full((len(var_trend),len(t0_periods)),np.nan)
            # trend_iso_fit[var]=np.full((len(var_trend),len(t0_periods)),np.nan)
            
            log('Calculation trend for '+var,indent=1)
            for kp in range(len(t0_periods)):       
                indprof=np.where(np.logical_and(database["time"]>t0_periods[kp],database["time"]<tf_periods[kp]))[0] 
                if len(indprof)>1:
                    #trendval=np.diff(prof_avg[:,indprof],axis=1)/(np.diff(database['time'][indprof])/(3600*24*365)) # x/yr
                    trend_avg[var][:,kp]=(prof_avg[:,indprof[-1]]-prof_avg[:,indprof[0]])/(database['time'][indprof[-1]]-database['time'][indprof[0]])*3600*24*365
                    trend_prof=np.full((len(depth_trend),),np.nan) # Profile of trends
                    R2_prof=np.full((len(depth_trend),),np.nan) # Profile of R2
                    intercept_prof=np.full((len(depth_trend),),np.nan) # Profile of intercept values
                    for kz in range(len(depth_trend)): 
                        if sum(~np.isnan(prof_avg[kz,indprof]))>nmin: # At least nmin samples
                            indval0=np.where(~np.isnan(prof_avg[kz,indprof]))[0][0]# First profile used
                            indvalf=np.where(~np.isnan(prof_avg[kz,indprof]))[0][-1]# Last profile used
                            if (database['time'][indprof[indvalf]]-database['time'][indprof[indval0]])>=mindur*365*24*3600: # At least duration of mindur years
                                pfit,_,R2=regression_oneline(database['time'][indprof]/(3600*24*365),prof_avg[kz,indprof])
                                trend_prof[kz]=pfit[0]
                                R2_prof[kz]=R2
                                intercept_prof[kz]=pfit[1]
                    trend_fit[var][:,kp]=trend_prof
                    R2_fit[var][:,kp]=R2_prof
                    intercept_fit[var][:,kp]=intercept_prof
                    
                    # Calculate trends of isolines movements
                    if var=="Temp":
                        zmin=100
                    else:
                        zmin=0
                    trend_iso_avg_var,trend_iso_fit_var,z_iso,var_trend=compute_iso_displacements(database['time'][indprof],database["depth_interp"],database[var],dvar[kvar],delta_smooth=10,zmin=zmin,dz=1,nmin=10,mindur=1)
                    if kp==0: # Define variables
                        trend_iso_avg[var]=np.full((len(trend_iso_avg_var),len(t0_periods)),np.nan)
                        trend_iso_fit[var]=np.full((len(trend_iso_fit_var),len(t0_periods)),np.nan)
                        z_iso_all[var]=np.full((len(var_trend),len(database["time"])),np.nan)
                        self.data[var.lower()+"_trend"]=var_trend
                    
                    z_iso_all[var][:,indprof]=z_iso
                    trend_iso_avg[var][:,kp]=trend_iso_avg_var
                    trend_iso_fit[var][:,kp]=trend_iso_fit_var
                    
                    # trend_iso_avg[var][:,kp]=(z_iso[:,indprof[-1]]-z_iso[:,indprof[0]])/(database['time'][indprof[-1]]-database['time'][indprof[0]])*3600*24*365 # m/yr
                    # trend_prof=np.full((len(var_trend),),np.nan) # Profile of trends
                    # for kz in range(len(var_trend)):
                    #     if sum(~np.isnan(z_iso[kz,indprof]))>nmin: # At least nmin samples
                    #         indval0=np.where(~np.isnan(z_iso[kz,indprof]))[0][0]# First profile used
                    #         indvalf=np.where(~np.isnan(z_iso[kz,indprof]))[0][-1]# Last profile used
                    #         if (database['time'][indprof[indvalf]]-database['time'][indprof[indval0]])>=mindur*365*24*3600: # At least duration of mindur years
                    #             pfit,_,_=regression_oneline(database['time'][indprof]/(3600*24*365),z_iso[kz,indprof])
                    #             trend_prof[kz]=pfit[0] # m/yr
                    # trend_iso_fit[var][:,kp]=trend_prof
            
            
            
            self.data["z_iso_"+var]=z_iso_all[var]
            self.data["trenddata_"+var]=prof_avg
            self.data["trendavg_"+var]=trend_avg[var]
            self.data["trendfit_"+var]=trend_fit[var]
            self.data["R2fit_"+var]=R2_fit[var]
            self.data["interceptfit_"+var]=intercept_fit[var]
            self.data["trendavg_iso_"+var]= trend_iso_avg[var]
            self.data["trendfit_iso_"+var]=trend_iso_fit[var]
            
        return trend_avg,trend_fit,z_iso_all
    
    
    
    
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
                # #if not isinstance(data[key], collections.Sized) and data[key]=='N/a': # Replace missing values by nan if the value is not an array of length>1
                # if isinstance(data[key], str) and data[key]=='N/a':     
                #     data[key]=np.nan 
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
        
        
    def zchem(self,database):
        """
        # Computes average chemocline depth as the depth of maximum density gradient 
        # (saved as "z_maxdens")
        #
        # Inputs: 
            # database: dictionary with the database quantities for all the profiles

        """
        self.data["z_chem"]=[np.nanmean(database["z_maxdens_smooth"][np.logical_and(database["time"]>self.data["time0_periods"][i],
                                                                      database["time"]<self.data["timef_periods"][i])]) for i in range(len(self.data["time0_periods"]))]