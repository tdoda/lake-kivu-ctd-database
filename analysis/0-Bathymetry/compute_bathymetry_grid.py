# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 18:57:43 2023

@author: dodatomy
"""


import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import cmocean
import xarray as xr
import geopandas as gpd
from shapely.geometry import Point, Polygon
from scipy.interpolate import griddata
from matplotlib import path

# adding Functions to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *

plt.close ('all')

#%% Load lake contour
lakecontour=gpd.read_file('..\..\..\..\Bathymetry\Kivu_Lake.shp')
breakpoint()
#%% Contour lines data
# bathdata=gpd.read_file('..\..\..\..\Bathymetry\Kivu_contourlines_corrected.shp')

# xdata=[None]*(len(bathdata)+1)
# ydata=[None]*(len(bathdata)+1)
# zdata=[None]*(len(bathdata)+1)

# for index,row in bathdata.iterrows():
#     print(str(index/len(bathdata)*100))
#     if row["geometry"] is None:
#         xdata[index]=np.nan
#         ydata[index]=np.nan
#         zdata[index]=np.nan
#     else:
#         if row["geometry"].geom_type=='MultiLineString':
#             xval=np.array([])
#             yval=np.array([])
#             for kline in range(len(row["geometry"].geoms)):
#                 xval=np.concatenate((xval,np.array([row["geometry"].geoms[kline].coords[i][0] for i in range(len(row["geometry"].geoms[kline].coords))])))
#                 yval=np.concatenate((yval,np.array([row["geometry"].geoms[kline].coords[i][1] for i in range(len(row["geometry"].geoms[kline].coords))])))
#             xdata[index]=xval
#             ydata[index]=yval
#         else:
#             xdata[index]=[row["geometry"].coords[i][0] for i in range(len(row["geometry"].coords))]
#             ydata[index]=[row["geometry"].coords[i][1] for i in range(len(row["geometry"].coords))]
#             zdata[index]=row["Meters"]
# xdata[index+1]=[lakecontour["geometry"][0].exterior.coords[i][0] for i in range(len(lakecontour["geometry"][0].exterior.coords))]
# ydata[index+1]=[lakecontour["geometry"][0].exterior.coords[i][1] for i in range(len(lakecontour["geometry"][0].exterior.coords))]
# zdata[index+1]=0

#%% Remove nan and sort data
# xdata=[xdata[k] for k in np.where(~np.isnan(zdata))[0]]
# ydata=[ydata[k] for k in np.where(~np.isnan(zdata))[0]]
# zdata=[zdata[k] for k in np.where(~np.isnan(zdata))[0]]
#%% Bathymetry grid

df=pd.read_csv('..\..\..\..\Bathymetry\Kivu_blend.xyz', header=0, names=['long','lat','z'],sep="\t",index_col=False,skiprows=1)
reso=0.001 # [°]
X,Y=np.mgrid[df["long"].min():df["long"].max():reso,df["lat"].min():df["lat"].max():reso]
dobs=1 # Affect the amount of data used to create the interpolation
print('Creation of the grid')
longval=df["long"].values[np.arange(0,len(df["long"]),dobs)]
latval=df["lat"].values[np.arange(0,len(df["long"]),dobs)]
zval=df["z"].values[np.arange(0,len(df["long"]),dobs)]


Z=griddata((longval,latval), zval, (X,Y), method='linear')


#%% Vertices of polygons
polycontour=Polygon(list(lakecontour["geometry"][0].exterior.coords)) # Outside contour
xcont,ycont=polycontour.exterior.xy
xpoly=[xcont]
ypoly=[ycont]
polyinner=[] # Islands
for intpoly in lakecontour["geometry"][0].interiors:
    polyinner.append(Polygon(list(intpoly.coords)))
    xcont,ycont=polyinner[-1].exterior.xy
    xpoly.append(xcont)
    ypoly.append(ycont)
#%% Remove points outside lake: method #1  
ind_shallow=np.where(Z>-100)  
Zcorr=Z.copy()

for kpoint in range(len(ind_shallow[0])):  
    print(kpoint/len(ind_shallow[0])*100)
    if not Point(X[ind_shallow[0][kpoint],ind_shallow[1][kpoint]],Y[ind_shallow[0][kpoint],ind_shallow[1][kpoint]]).within(polycontour):
        Zcorr[ind_shallow[0][kpoint],ind_shallow[1][kpoint]]=np.nan
    else:
        for kpoly in range(len(polyinner)):
            if Point(X[ind_shallow[0][kpoint],ind_shallow[1][kpoint]],Y[ind_shallow[0][kpoint],ind_shallow[1][kpoint]]).within(polyinner[kpoly]):
                Zcorr[ind_shallow[0][kpoint],ind_shallow[1][kpoint]]=np.nan
                
#%% Remove points outside lake: method #2
ind_shallow=np.where(Z>-200)
path_contour = path.Path(list(lakecontour["geometry"][0].exterior.coords)) 
coord_shallow=[]
Zcorr2=Z.copy()
for kpoint in range(len(ind_shallow[0])): 
    #print('Progress (points) {:.2f} %'.format(kpoint/len(ind_shallow[0])*100))
    coord_shallow.append((X[ind_shallow[0][kpoint],ind_shallow[1][kpoint]],Y[ind_shallow[0][kpoint],ind_shallow[1][kpoint]]))  
print('Detect points outside lake')
bool_outside=path_contour.contains_points(coord_shallow)
ind_outside=np.where(np.logical_not(bool_outside))[0]

# Islands
ind_remaining=np.where(bool_outside)[0]
coord_remaining=[coord_shallow[ind_remaining[i]] for i in range(len(ind_remaining))]
ind_inside=np.array([])
for kpoly in range(len(lakecontour["geometry"][0].interiors)):
    print('Progress (polygons) {:.2f} %'.format(kpoly/len(polyinner)*100))
    path_inside=path.Path(list(lakecontour["geometry"][0].interiors[kpoly].coords)) 
    ind_inside=np.concatenate((ind_inside,np.where(path_inside.contains_points(coord_remaining))[0]))

ind_nan=np.concatenate((ind_outside,ind_remaining[ind_inside.astype(int)]))
for kpoint in ind_nan:
    Zcorr2[ind_shallow[0][kpoint],ind_shallow[1][kpoint]]=np.nan
        
#%% Plot
fig,ax=plt.subplots()
hmesh=ax.pcolormesh(X,Y,Zcorr2)
#lakecontour.plot(ax=ax)
cb=plt.colorbar(hmesh)

# Add boundaries:
for kpoly in range(len(xpoly)):
    ax.plot(xpoly[kpoly],ypoly[kpoly],'-k',linewidth=0.5)
ax.axis('equal')
#%% Save data as csv file

df_Z=pd.DataFrame(Zcorr2.transpose())
df_Z.columns=X[:,0]
df_Z.index=Y[0,:]
df_Z.to_csv('bathymetry_grid_'+str(int(reso*1000))+'mdeg_'+str(dobs)+'dobs.csv', sep=",")
