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
            "depth_interp": {'dim_name': "depth_interp", 'dim_size': None},
            "bounds": {'dim_name': "bounds", 'dim_size': 2}
        }

        # Create variables: primary keys should match name of variables in the script and var_name is the variable name in netCDF file
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
            "rho_top": {'var_name': "rho_top", 'dim': ('time',), 'unit': 'kg.m^(-3)', 'longname': 'Density of the upper layer'},
            "rho_bot": {'var_name': "rho_bot", 'dim': ('time',), 'unit': 'kg.m^(-3)', 'longname': 'Density of the lower layer'},
            "z_bounds": {'var_name': "z_bounds", 'dim': ('bounds',), 'unit': 'm', 'longname': 'Depth bounds of the fitted profile'},
            "z_maxdens": {'var_name': 'z_maxdens', 'dim': ('time',), 'unit': 'm', 'longname': 'Depth of maxmimum density gradient'},
            "z_maxdens_smooth": {'var_name': 'z_maxdens_smooth', 'dim': ('time',), 'unit': 'm', 'longname': 'Depth of maxmimum density gradient (smoothed)'},
            "z_meta_middle": {'var_name': 'z_meta_middle', 'dim': ('time',), 'unit': 'm', 'longname': 'Mean depth of the metalimnion'},
            "z_middens": {'var_name': "z_middens", 'dim': ('time',), 'unit': 'm', 'longname': 'Chemocline depth based on surface and bottom mean densities'},
            "z_chemfit": {'var_name': 'z_chemfit', 'dim': ('time',), 'unit': 'm', 'longname': 'Chemocline depth from fitted profile'},
            "delta_metafit": {'var_name': 'delta_metafit', 'dim': ('time',), 'unit': 'm', 'longname': 'Thickness of the metalimnion from fitted profile'},
            "z_therm": {'var_name': 'z_therm', 'dim': ('time',), 'unit': 'm', 'longname': 'Thermocline depth'},
            "Sc": {'var_name': 'Sc', 'dim': ('time',), 'unit': 'J.m-2', 'longname': 'Schmidt stability'},
            "trendprof_Temp": {'var_name': 'trendprof_Tem', 'dim': ('depth_interp', 'time'), 'unit': 'degC/yr', 'longname': 'Temnperature trends with respect to reference period'},
            "trendprof_Cond": {'var_name': 'trendprof_Cond', 'dim': ('depth_interp', 'time'), 'unit': 'mS/cm/yr', 'longname': 'Conductivity dtrends with respect to reference period'},
            "trendprof_rho": {'var_name': 'trendprof_rho', 'dim': ('depth_interp', 'time'), 'unit': 'kg/m3/yr', 'longname': 'Density trends with respect to reference period'},
        }
        
        self.data = {}

    def compute_maxdens(self,zmin=220,zmax=300):
        """
        # Computes chemocline depth as the depth of maximum density gradient 
        # (saved as "z_maxdens")
        #
        # Inputs: 
            # zmin [m]: minimum depth of the profile to analyze
            # zmax [m]: maximum depth of the profile to analyze
        """
        rhoval=self.data["rho"][np.logical_and(self.data["depth_interp"]>=zmin,self.data["depth_interp"]<=zmax),:]
        boolnan=np.sum(np.isnan(rhoval),axis=0)==rhoval.shape[0]
        self.data["z_maxdens"]=np.array([np.nan]*rhoval.shape[1])

        grad_rho=np.abs(np.gradient(rhoval, axis=0))
        depthval=self.data["depth_interp"][np.logical_and(self.data["depth_interp"]>=zmin,self.data["depth_interp"]<=zmax)]
        self.data["z_maxdens"][~boolnan]=depthval[np.nanargmax(grad_rho[:,~boolnan],axis=0)]
        
        
    def compute_metalimnion(self,grad_threshold=0.07,windowsize=10,zmin=220,zmax=300):
        """
        # Finds upper and lower bounds of metalimnion based on density gradient
        # from smoothed density profile. The depth of maximum gradient is saved as
        # "z_maxdens_smooth" and the average depth of the metalimnion as 
        # "z_meta_middle".
        #
        # Inputs:
            # grad_threshold [kg.m^(-3).m^(-1)]: gradient threshold defining the upper and lower bounds of the metalimnion 
            # windowsize: window size used to smooth the profile
            # zmin [m]: minimum depth of the profile to analyze
            # zmax [m]: maximum depth of the profile to analyze
        """
        dz=np.expand_dims(self.data["depth_interp"][2:]-self.data["depth_interp"][:-2],axis=1)
        # Create smooth density:
        # rho_smooth=np.full(self.data["rho"].shape,np.nan)
        # for k in range(len(self.data["time"])): 
        #     df=pd.DataFrame({'rho':self.data["rho"][:,k]})
        #     rho_smooth[:,k]=df.rolling(windowsize).mean().values[:,0]
        rho_smooth=movmean(self.data["rho"],windowsize)
        grad_rho=(rho_smooth[2:,:]-rho_smooth[:-2,:])/dz # [kg.m-3.m-1]
        zval=self.data["depth_interp"][1:-1]
        grad_rho=grad_rho[np.logical_and(zval>=zmin,zval<=zmax),:]
        zval=zval[np.logical_and(zval>=zmin,zval<=zmax)]
        indnonan=np.where(np.sum(np.isnan(grad_rho),axis=0)<grad_rho.shape[0])[0]
        
        zmax=np.full((grad_rho.shape[1],),np.nan)
        ztop=np.full((grad_rho.shape[1],),np.nan)
        zbot=np.full((grad_rho.shape[1],),np.nan)
        for k in indnonan:
            #df=pd.DataFrame({'Grad':grad_rho[:,k]})
            #grad_smooth=df.rolling(windowsize).mean().values
            # indmax=np.nanargmax(grad_smooth,axis=0)[0]
            grad_smooth=grad_rho[:,k]
            indmax=np.nanargmax(grad_smooth,axis=0)
            zmax[k]=zval[indmax]
            indtop=np.where(grad_smooth[:indmax]<grad_threshold)[0]
            indbot=indmax+np.where(grad_smooth[indmax:]<grad_threshold)[0]
            if np.any(indtop): # Not empty
                ztop[k]=zval[indtop[-1]]
            if np.any(indbot):
                zbot[k]=zval[indbot[0]]
        self.data["z_maxdens_smooth"]=zmax
        self.data["z_meta_middle"]=np.mean([zbot,ztop],axis=0)
        #return zmax,ztop,zbot
        
    def compute_chemfit(self,dz=10,windowsize=10,param=[10,260],zmin=230,zmax=280):
        """
        # Computes the chemocline depth based on a symmetrical function, i.e. 
        # as the middle point between surface and bottom densities (saved as "z_middens" and "z_chemfit" with fitting).
        #
        # Inputs:
            # dz [m]: thickness of the layer where surface and bottom densities are calculated
            # windowsize: window size used to smooth the profile
            # param=[delta,zchem] [m]: initial guess for the parameters
            # zmin [m]: minimum depth of the profile to analyze
            # zmax [m]: maximum depth of the profile to analyze
        """
        rho_smooth=movmean(self.data["rho"],windowsize,axis=0)
        zchemval=np.full((rho_smooth.shape[1],),np.nan)
        maxdepth=self.data["depth_interp"][[np.where(~np.isnan(rho_smooth[:,k]))[0][-1] for k in range(rho_smooth.shape[1])]]
        keepprof=maxdepth>zmax
        rho_smooth=rho_smooth[:,keepprof]
        rho_top=np.nanmean(rho_smooth[np.logical_and(self.data["depth_interp"]>=zmin,self.data["depth_interp"]<=zmin+dz),:],axis=0)
        rho_bot=np.nanmean(rho_smooth[np.logical_and(self.data["depth_interp"]>=zmax-dz,self.data["depth_interp"]<=zmax),:],axis=0)
        zchemval[keepprof]=np.array([self.data["depth_interp"][np.where(rho_smooth[:,k]>=np.mean([rho_top[k],rho_bot[k]],axis=0))[0][0]] for k in range(len(rho_top))])
        self.data["bounds"]=np.array([0,1])
        self.data["z_bounds"]=np.array([zmin,zmax])
        self.data["rho_top"]=np.full(zchemval.shape,np.nan)
        self.data["rho_top"][keepprof]=rho_top
        self.data["rho_bot"]=np.full(zchemval.shape,np.nan)
        self.data["rho_bot"][keepprof]=rho_bot
        self.data["z_middens"]=zchemval
        
        # zchemfit=np.full((rho_smooth.shape[1],),np.nan)
        # deltafit=np.full((rho_smooth.shape[1],),np.nan)
        # for kt in range(rho_smooth.shape[1]):
        #     # Fitting function:
        #     def densfunc(z,delta,zchem): 
        #         # z>0 downward
        #         return rho_top[kt]+(rho_bot[kt]-rho_top[kt])/2*(np.tanh((z-zchem)/delta)+1)
        #     keepdepth=np.logical_and.reduce((~np.isnan(rho_smooth[:,kt]),self.data["depth_interp"]>=zmin,self.data["depth_interp"]<=zmax))
        #     param,_= curve_fit(densfunc, self.data["depth_interp"][keepdepth],rho_smooth[keepdepth,kt],p0=param)
        #     zchemfit[kt]=param[1]
        #     deltafit[kt]=param[0]
        zchemfit, deltafit,_,_=fit_rho(self.data["depth_interp"],rho_smooth,rho_top,rho_bot,[zmin,zmax],param)

        self.data["z_chemfit"]=np.full(zchemval.shape,np.nan)
        self.data["z_chemfit"][keepprof]=zchemfit
        
        self.data["delta_metafit"]=np.full(zchemval.shape,np.nan)
        self.data["delta_metafit"][keepprof]=deltafit
    
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