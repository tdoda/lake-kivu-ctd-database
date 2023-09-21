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
            "z_centermass": {'var_name': 'z_centermass', 'dim': ('time',), 'unit': 'm', 'longname': 'Center of mass of the layer near chemocline (z_bounds)'},
            "delta_metafit": {'var_name': 'delta_metafit', 'dim': ('time',), 'unit': 'm', 'longname': 'Thickness of the metalimnion from fitted profile'},
            "z_therm": {'var_name': 'z_therm', 'dim': ('time',), 'unit': 'm', 'longname': 'Thermocline depth'},
            "N2": {'var_name': 'N2', 'dim': ('depth_interp','time'), 'unit': 's-2', 'longname': 'Squared buoyancy frequency'},
            "Sc_Read": {'var_name': 'Sc_Read', 'dim': ('time',), 'unit': 'J', 'longname': 'Schmidt stability with respect to center of volume (layer 2-300 m)'},
            "Sc_Imb": {'var_name': 'Sc_Imb', 'dim': ('time',), 'unit': 'J', 'longname': 'Schmidt stability with respect to center of volume and mixed profile (layer 2-300 m)'},
            "Sc": {'var_name': 'Sc', 'dim': ('time',), 'unit': 'J.m-2', 'longname': 'Schmidt stability from pylake'},
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
    
    def compute_centermass(self,hypso_z=[],hypso_A=[],zmin=230,zmax=280):
        zval=self.data["depth_interp"][np.logical_and(self.data["depth_interp"]>=zmin,self.data["depth_interp"]<=zmax)].reshape(-1,1)       
        rhoval=self.data["rho"][np.logical_and(self.data["depth_interp"]>=zmin,self.data["depth_interp"]<=zmax),:]
        
        # Including lake area
        if np.any(hypso_z):
            Aval=np.interp(zval,hypso_z,hypso_A)
            total_mass=np.trapz(rhoval*Aval,zval,axis=0)
            self.data["z_centermass"]=1/total_mass*np.trapz(rhoval*Aval*zval,zval,axis=0)
        else:
        # Without including lake area
            total_mass=np.trapz(rhoval,zval,axis=0)
            self.data["z_centermass"]=1/total_mass*np.trapz(rhoval*zval,zval,axis=0)
        
    def compute_N2_database(self,windowsize=10,g=9.81):
        # zval increases downward
        zval=self.data["depth_interp"].reshape(-1,1)
        rho_smooth=movmean(self.data["rho"],windowsize,axis=0)
         
        rho0=np.nanmean(rho_smooth,axis=0)
        N2=np.full(rho_smooth.shape,np.nan)
        N2[1:,:]=1/rho0*np.diff(rho_smooth,axis=0)/np.diff(zval,axis=0)*g
        self.data["N2"]=N2
        return N2 
    
    def compute_Sc_database(self,hypso_z,hypso_A,zmin=1,zmax=300,g=9.81):
        # zval increases downward
        zval=self.data["depth_interp"].reshape(-1,1)
        rhoval=self.data["rho"]
        rhomean=np.nanmean(rhoval,axis=0)
        Aval=np.interp(zval,hypso_z,hypso_A)
        zv=np.trapz(zval*Aval,zval,axis=0)/np.trapz(Aval,zval,axis=0)
        Sc_Read=np.array([np.nan]*rhoval.shape[1]) # J
        Sc_Imb=np.array([np.nan]*rhoval.shape[1]) # J
        for kt in range(len(Sc_Read)):
            if self.data["max_depth"][kt]>=zmax and self.data["min_depth"][kt]<=zmin:
                valkeep=np.logical_and(~np.isnan(rhoval[:,kt]),np.logical_and(zval[:,0]>=zmin,zval[:,0]<=zmax))
                Sc_Read[kt]=g*np.trapz((zval[valkeep][:,0]-zv)*rhoval[valkeep,kt]*Aval[valkeep][:,0],zval[valkeep][:,0],axis=0)
                Sc_Imb[kt]=g*np.trapz((zval[valkeep][:,0]-zv)*(rhoval[valkeep,kt]-rhomean[kt])*Aval[valkeep][:,0],zval[valkeep][:,0],axis=0)
        self.data["Sc_Read"]=Sc_Read
        self.data["Sc_Imb"]=Sc_Imb
        return Sc_Read, Sc_Imb 
        
    
    
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
            "temp_trend":{'var_name': "temp_trend", 'dim': ('temp_trend',), 'unit': '°C', 'longname': "Temperature values for isotherms displacements"},
            "z_iso_Temp":{'var_name': "z_iso_Temp", 'dim': ('temp_trend','time'), 'unit': 'm', 'longname': "Depth of isotherms"},
            "trendavg_iso_Temp":{'var_name': "trendavg_iso_Temp", 'dim': ('temp_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average isotherms displacements"},
            "trendfit_iso_Temp":{'var_name': "trendfit_iso_Temp", 'dim': ('temp_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Isotherms displacements from linear fit"},
            
            "meanprof_Cond_avg":{'var_name': "meanprof_Cond_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm', 'longname': "Mean conductivity profile"},
            "meanprof_Cond_std":{'var_name': "meanprof_Cond_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'mS/cm', 'longname': "Profile of conductivity std"}, 
            "trendavg_Cond":{'var_name': "trendavg_Cond", 'dim': ('depth_trend','time0_periods'), 'unit': 'mS.cm-1.yr-1', 'longname': "Average conductivity trend"},
            "trendfit_Cond":{'var_name': "trendfit_Cond", 'dim': ('depth_trend','time0_periods'), 'unit': 'mS.cm-1.yr-1', 'longname': "Conductivity trend from linear fit"},
            "cond_trend":{'var_name': "cond_trend", 'dim': ('cond_trend',), 'unit': 'mS.cm-1', 'longname': "Conductivity values for isolines displacements"},
            "z_iso_Cond":{'var_name': "z_iso_Cond", 'dim': ('cond_trend','time'), 'unit': 'm', 'longname': "Depth of conductivity isolines"},
            "trendavg_iso_Cond":{'var_name': "trendavg_iso_Cond", 'dim': ('cond_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average conductivity isolines displacements"},
            "trendfit_iso_Cond":{'var_name': "trendfit_iso_Cond", 'dim': ('cond_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Conductivity isolines displacements from linear fit"},
                       
            "meanprof_SALIN_avg":{'var_name': "meanprof_SALIN_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'g/kg', 'longname': "Mean salinity profile"},
            "meanprof_SALIN_std":{'var_name': "meanprof_SALIN_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'g/kg', 'longname': "Profile of salinity std"}, 
            "trendavg_SALIN":{'var_name': "trendavg_SALIN", 'dim': ('depth_trend','time0_periods'), 'unit': 'g.kg-1.yr-1', 'longname': "Average salinity trend"},
            "trendfit_SALIN":{'var_name': "trendfit_SALIN", 'dim': ('depth_trend','time0_periods'), 'unit': 'g.kg-1.yr-1', 'longname': "Salinity trend from linear fit"},
            "salin_trend":{'var_name': "salin_trend", 'dim': ('salin_trend',), 'unit': 'g/kg', 'longname': "Salinity values for isohalines displacements"},
            "z_iso_SALIN":{'var_name': "z_iso_SALIN", 'dim': ('salin_trend','time'), 'unit': 'm', 'longname': "Depth of isohalines"},
            "trendavg_iso_SALIN":{'var_name': "trendavg_iso_SALIN", 'dim': ('salin_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average isohalines displacements"},
            "trendfit_iso_SALIN":{'var_name': "trendfit_iso_SALIN", 'dim': ('salin_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Isohalines displacements from linear fit"},
                        
            "meanprof_rho_avg":{'var_name': "meanprof_rho_avg", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3', 'longname': "Mean density profile"},
            "meanprof_rho_std":{'var_name': "meanprof_rho_std", 'dim': ('depth_interp','time0_periods'), 'unit': 'kg/m3', 'longname': "Profile of density std"},  
            "trendavg_rho":{'var_name': "trendavg_rho", 'dim': ('depth_trend','time0_periods'), 'unit': 'kg.m-3.yr-1', 'longname': "Average density trend"},
            "trendfit_rho":{'var_name': "trendfit_rho", 'dim': ('depth_trend','time0_periods'), 'unit': 'kg.m-3.yr-1', 'longname': "Density trend from linear fit"},           
            "rho_trend":{'var_name': "rho_trend", 'dim': ('rho_trend',), 'unit': 'kg.m-3', 'longname': "Density values for isopycnals displacements"},
            "z_iso_rho":{'var_name': "z_iso_rho", 'dim': ('rho_trend','time'), 'unit': 'm', 'longname': "Depth of isopycnals"},
            "trendavg_iso_rho":{'var_name': "trendavg_iso_rho", 'dim': ('rho_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Average ispoyncals displacements"},
            "trendfit_iso_rho":{'var_name': "trendfit_iso_rho", 'dim': ('rho_trend','time0_periods'), 'unit': 'm.yr-1', 'longname': "Ispoyncals displacements from linear fit"},
            }
        
        self.data = {}
        
        
    # def compute_avgprof_3p(self,database,period_ref=[datetime(2008,1,1),datetime(2011,1,1)],date_extraction=datetime(2016,1,1)):
    #     # Average reference profile
    #     self.data["depth_interp"]=database.data["depth_interp"]
        
    #     tperiod_ref=[period_ref[k].replace(tzinfo=timezone.utc).timestamp() for k in [0,1]]
    #     textraction=date_extraction.replace(tzinfo=timezone.utc).timestamp()
    #     self.data["time0_periods"]=np.array([tperiod_ref[0],tperiod_ref[1],textraction])
    #     self.data["timef_periods"]=np.array([tperiod_ref[1],textraction,np.max(database.data["time"])])
    #     indprof_ref=np.where(np.logical_and(database.data["time"]>tperiod_ref[0],database.data["time"]<tperiod_ref[1]))[0]
    #     indprof_p1=np.where(np.logical_and(database.data["time"]>tperiod_ref[1],database.data["time"]<textraction))[0]
    #     indprof_p2=np.where(database.data["time"]>=textraction)[0]
    #     prof_avg=dict()
    #     prof_trend=dict()
    #     prof_trendavg=dict()
        
    #     for var in ["Temp","Cond","rho"]:
    #         prof_avg[var+"_ref"]=np.nanmean(database.data[var][:,indprof_ref],axis=1)
    #         prof_avg[var+"_ref_std"]=np.nanstd(database.data[var][:,indprof_ref],axis=1)
    #         prof_avg[var+"_p1"]=np.nanmean(database.data[var][:,indprof_p1],axis=1)
    #         prof_avg[var+"_p1_std"]=np.nanstd(database.data[var][:,indprof_p1],axis=1)
    #         prof_avg[var+"_p2"]=np.nanmean(database.data[var][:,indprof_p2],axis=1)
    #         prof_avg[var+"_p2_std"]=np.nanstd(database.data[var][:,indprof_p2],axis=1)
    #         refprof=prof_avg[var+"_ref"][:,np.newaxis]
    #         prof_trend[var]=(database.data[var]-refprof)/((database.data["time"]-np.mean(tperiod_ref))/(3600*24*365))
    #         # prof_trendavg[var+"_p1"]=np.nanmean(prof_trend[var][:,indprof_p1],axis=1)
    #         # prof_trendavg[var+"_p1_std"]=np.nanstd(prof_trend[var][:,indprof_p1],axis=1)
    #         # prof_trendavg[var+"_p2"]=np.nanmean(prof_trend[var][:,indprof_p2],axis=1)
    #         # prof_trendavg[var+"_p2_std"]=np.nanstd(prof_trend[var][:,indprof_p2],axis=1)
            
            
    #         trend_p1=(database.data[var][:,indprof_p1[1:]]-database.data[var][:,indprof_p1[0]][:,np.newaxis])/((database.data["time"][indprof_p1[1:]]-database.data["time"][indprof_p1[0]])/(3600*24*365))
    #         trend_p2=(database.data[var][:,indprof_p2[1:]]-database.data[var][:,indprof_p2[0]][:,np.newaxis])/((database.data["time"][indprof_p2[1:]]-database.data["time"][indprof_p2[0]])/(3600*24*365))
    #         prof_trendavg[var+"_p1"]=np.nanmean(trend_p1,axis=1)
    #         prof_trendavg[var+"_p1_std"]=np.nanstd(trend_p1,axis=1)
    #         prof_trendavg[var+"_p2"]=np.nanmean(trend_p2,axis=1)
    #         prof_trendavg[var+"_p2_std"]=np.nanstd(trend_p2,axis=1)
            
    #         self.data["meanprof_"+var+"_avg"]=np.concatenate((prof_avg[var+"_ref"][:,np.newaxis],prof_avg[var+"_p1"][:,np.newaxis],prof_avg[var+"_p2"][:,np.newaxis]),axis=1)
    #         self.data["meanprof_"+var+"_std"]=np.concatenate((prof_avg[var+"_ref_std"][:,np.newaxis],prof_avg[var+"_p1_std"][:,np.newaxis],prof_avg[var+"_p2_std"][:,np.newaxis]),axis=1)
    #         database.data["trendprof_"+var]=prof_trend[var]
    #         self.data["meantrendprof_"+var+"_avg"]=np.concatenate((np.zeros((len(database.data["depth_interp"]),1)),prof_trendavg[var+"_p1"][:,np.newaxis],prof_trendavg[var+"_p2"][:,np.newaxis]),axis=1)
    #         self.data["meantrendprof_"+var+"_std"]=np.concatenate((np.zeros((len(database.data["depth_interp"]),1)),prof_trendavg[var+"_p1_std"][:,np.newaxis],prof_trendavg[var+"_p2_std"][:,np.newaxis]),axis=1)
        
    #     return prof_avg, prof_trend,prof_trendavg
    
    
    
    def compute_avgprof(self,database,t0_periods,tf_periods,varnames=["Temp","Cond","SALIN","rho"]):
        # t0_periods: initial time of each period
        # tf_periods: final time of each period
        
        
        # Convert datetime periods into timestamp:
        t0_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in t0_periods])
        tf_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in tf_periods])
        
        
        self.data["depth_interp"]=database.data["depth_interp"]
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
                indprof=np.where(np.logical_and(database.data["time"]>t0_periods[kp],database.data["time"]<tf_periods[kp]))[0]   
                prof_avg[var][:,kp]=np.nanmean(database.data[var][:,indprof],axis=1)
                prof_std[var][:,kp]=np.nanstd(database.data[var][:,indprof],axis=1)
                # trendval=np.diff(database.data[var][:,indprof],axis=1)/(np.diff(database.data['time'][indprof])/(3600*24*365)) # x/yr
                # trend_avg[var][:,kp]=np.nanmean(trendval,axis=1)
                # trend_std[var][:,kp]=np.nanstd(trendval,axis=1) 
                # trend_prof=np.full((len(database.data["depth_interp"]),),np.nan) # Profile of trends
                # for kz in range(len(database.data["depth_interp"])): 
                #     if sum(np.isnan(database.data[var][kz,indprof]))<len(indprof)-2: # At least 3 samples
                #         pfit,_,_=regression_oneline(database.data['time'][indprof]/(3600*24*365),database.data[var][kz,indprof])
                #         trend_prof[kz]=pfit[0]
                # trend_fit[var][:,kp]=trend_prof
                
            self.data["meanprof_"+var+"_avg"]=prof_avg[var]
            self.data["meanprof_"+var+"_std"]=prof_std[var]
            
        return prof_avg, prof_std
    
    
    
    def compute_avgtrend(self,database,t0_periods,tf_periods,dz,dvar=[0.01,0.01,0.01,0.01],varnames=["Temp","Cond","SALIN","rho"]):
        # t0_periods: initial time of each period
        # tf_periods: final time of each period
        # dz: new depth step to compute trend
        # drho: density step for trends of isopycnals location
        
        # Convert datetime periods into timestamp:
        t0_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in t0_periods])
        tf_periods=np.array([dateval.replace(tzinfo=timezone.utc).timestamp() for dateval in tf_periods])
        
        depth_trend=np.arange(self.data["depth_interp"][0],self.data["depth_interp"][-1],dz)
        # temp_trend=np.arange(round(np.nanmin(database.data["Temp"])/dT)*dT,round(np.nanmax(database.data["Temp"])/dT)*dT,dT)
        # cond_trend=np.arange(round(np.nanmin(database.data["Cond"])/dC)*dC,round(np.nanmax(database.data["Cond"])/dC)*dC,dC)
        # salin_trend=np.arange(round(np.nanmin(database.data["SALIN"])/dS)*dS,round(np.nanmax(database.data["SALIN"])/dS)*dS,dS)
        # rho_trend=np.arange(round(np.nanmin(database.data["rho"])/drho)*drho,round(np.nanmax(database.data["rho"])/drho)*drho,drho)
        
        
        self.data["depth_trend"]=depth_trend
        self.data["time"]=database.data["time"]
        if "time0_periods" not in self.data.keys():
            self.data["time0_periods"]=t0_periods
            self.data["timef_periods"]=tf_periods
        
        
        trend_avg=dict()
        trend_fit=dict()
        trend_iso_avg=dict()
        trend_iso_fit=dict()
        
        
        kvar=-1
        for var in varnames:
            kvar+=1
            nlayers=round((self.data["depth_interp"][-1]-self.data["depth_interp"][0])/dz)
            nval=round(dz/(self.data["depth_interp"][1]-self.data["depth_interp"][0]))
            prof_avg=np.mean(database.data[var].reshape((nval,-1),order='F'),axis=0).reshape((nlayers,-1),order='F') # Profile with new z resolution(depth_trend), averages in each layer
            trend_avg[var]=np.full((len(depth_trend),len(t0_periods)),np.nan)
            trend_fit[var]=np.full((len(depth_trend),len(t0_periods)),np.nan)
            
            # Create matrix with isolines positions
            var_trend=np.arange(round(np.nanmin(database.data[var])/dvar[kvar])*dvar[kvar],round(np.nanmax(database.data[var])/dvar[kvar])*dvar[kvar],dvar[kvar])
            self.data[var.lower()+"_trend"]=var_trend
            z_iso=np.full((len(var_trend),len(database.data["time"])),np.nan)
            data_smooth=movmean(database.data[var],10,axis=1) # Temporal smoothening
            for kp in range(len(database.data["time"])):
                # Get location of isolines: could be problematic when non monotic changes in the data (several locations for the same isoline)
                # Do not consider the upper 100 m for temperature because decreasing T with depth
                data_prof=data_smooth[:,kp]
                if var=="Temp":
                    data_prof[database.data["depth_interp"]<100]=np.nan
                indsort=np.argsort(data_prof) # Sort values
                z_iso[:,kp]=np.interp(var_trend,data_prof[indsort],database.data["depth_interp"][indsort]) 
            trend_iso_avg[var]=np.full((len(var_trend),len(t0_periods)),np.nan)
            trend_iso_fit[var]=np.full((len(var_trend),len(t0_periods)),np.nan)
            
            log('Calculation trend for '+var,indent=1)
            for kp in range(len(t0_periods)):       
                indprof=np.where(np.logical_and(database.data["time"]>t0_periods[kp],database.data["time"]<tf_periods[kp]))[0]   
                if len(indprof)>1:
                    #trendval=np.diff(prof_avg[:,indprof],axis=1)/(np.diff(database.data['time'][indprof])/(3600*24*365)) # x/yr
                    trend_avg[var][:,kp]=(prof_avg[:,indprof[-1]]-prof_avg[:,indprof[0]])/(database.data['time'][indprof[-1]]-database.data['time'][indprof[0]])*3600*24*365
                    trend_prof=np.full((len(depth_trend),),np.nan) # Profile of trends
                    for kz in range(len(depth_trend)): 
                        if sum(np.isnan(prof_avg[kz,indprof]))<len(indprof)-2: # At least 3 samples
                            pfit,_,_=regression_oneline(database.data['time'][indprof]/(3600*24*365),prof_avg[kz,indprof])
                            trend_prof[kz]=pfit[0]
                    trend_fit[var][:,kp]=trend_prof
                    
                    
                    # Calculate trends of isolines movements
                    trend_iso_avg[var][:,kp]=(z_iso[:,indprof[-1]]-z_iso[:,indprof[0]])/(database.data['time'][indprof[-1]]-database.data['time'][indprof[0]])*3600*24*365 # m/yr
                    trend_prof=np.full((len(var_trend),),np.nan) # Profile of trends
                    for kz in range(len(var_trend)): 
                        if sum(np.isnan(z_iso[kz,indprof]))<len(indprof)-2: # At least 3 samples
                            pfit,_,_=regression_oneline(database.data['time'][indprof]/(3600*24*365),z_iso[kz,indprof])
                            trend_prof[kz]=pfit[0] # m/yr
                    trend_iso_fit[var][:,kp]=trend_prof
             
            self.data["z_iso_"+var]=z_iso
            self.data["trendavg_"+var]=trend_avg[var]
            self.data["trendfit_"+var]=trend_fit[var]
            self.data["trendavg_iso_"+var]=trend_iso_avg[var]
            self.data["trendfit_iso_"+var]=trend_iso_fit[var]
            
        return trend_avg,trend_fit
    
    
    
    
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