# -*- coding: utf-8 -*-
"""
Created on Tue May 30 17:07:58 2023

@author: dodatomy
"""
import netCDF4
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timezone
import math
import cmocean
from geopy import distance
from scipy.stats import cumfreq
from scipy.interpolate import griddata
import shapefile
# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *



#%%
# Bathymetry (coordinates are not lat and lon!)
sf = shapefile.Reader("../../../../Bathymetry/Kivu_bath_WGS84.shp")
contour_data=sf.shapes()
attributes_data=sf.records()
xval=[]
yval=[]
zval=np.full(len(contour_data),np.nan)
for k in np.arange(0,len(contour_data),1):
    xval.append([i[0] for i in contour_data[k].points[:]])
    yval.append([i[1] for i in contour_data[k].points[:]])
    zval[k]=attributes_data[k][-1]
#     if zval[k]==20:
#         ax.plot(xval[k],yval[k],'.-')
zval_unique=np.unique(zval)

#%% Zero contour line
mindepth=np.min(zval_unique)
indcont=np.where(zval==mindepth)[0]
xval0=[]
yval0=[]
for k in indcont:
    xval0.append(xval[k])
    yval0.append(yval[k])
xval0_array=np.array(xval0[0])
yval0_array=np.array(yval0[0])

#%% xval_corr,yval_corr=sort_paths(xval0_array,yval0_array)
xval_corr=[None]*len(xval)
yval_corr=[None]*len(xval)
for k in range(len(xval)):
    print(k)
    #xval_corr,yval_corr=sort_paths(np.array(xval[k]),np.array(yval[k]))
    xval_corr[k],yval_corr[k]=divide_paths(np.array(xval[k]),np.array(yval[k]))

#%% Zero contour line
mindepth=np.min(zval_unique)
indcont=np.where(zval==mindepth)[0]
xval0=[]
yval0=[]
for k in indcont:
    xval0.append(xval[k])
    yval0.append(yval[k])
xval0_corr,yval0_corr=sort_paths(np.array(xval0[0]),np.array(yval0[0]))
