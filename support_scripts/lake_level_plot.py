# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 17:34:03 2022

@author: thomitob
"""
import json
import pandas as pd
import matplotlib.pyplot as plt

with open("../data/lake_level/c_gls.json") as f:
    data1=json.load(f)
dates = [i['datetime'] for i in data1["data"]]
values = [i['water_surface_height_above_reference_datum'] for i in data1['data']]
df = pd.DataFrame({'Date':dates, 'Waterlevel':values})
df['Date']  = (pd.to_datetime(df['Date'],format='%Y/%m/%d')) 


headers = ['Date', 'Waterlevel', 'Error']
df1 = pd.read_csv('../data/lake_level/dahiti.txt',skiprows=15,delimiter=' ',names=headers)
df1["Date"] = pd.to_datetime(df1["Date"],format="%Y-%m-%d")



headers = ['Date', 'Waterlevel']
df2 = pd.read_csv('../data/lake_level/bukavu.csv',delimiter=';', skiprows=1, names=headers)
df2["Date"] = pd.to_datetime(df2["Date"],format="%d.%m.%Y")



fig, ax = plt.subplots()

ax.plot(df["Date"], df["Waterlevel"], linewidth=0.7, color="blue", label='CGLS')
ax.scatter(df["Date"], df["Waterlevel"], s=3, color="blue")

ax.plot(df1["Date"], df1["Waterlevel"], linewidth=0.7, color="orange",label='DAHITI')
ax.scatter(df1["Date"], df1["Waterlevel"], s=3, color="orange",)

ax.plot(df2["Date"], df2["Waterlevel"], lw=0.7, color="red", label='In-situ (SNEL, Bukavu)')
ax.scatter(df2["Date"], df2["Waterlevel"], s=1, color="red",)

ax.plot(df2["Date"], df2["Waterlevel"]-1.2161909999999807, linewidth=0.7, color="green", label='In-situ (SNEL, Bukavu) adjusted by -1.216m')


ax.set_ylabel('Water level (m a.s.l.)',fontsize='x-large')
ax.set_xlabel('Date',fontsize='x-large')
ax.legend(fontsize='large')


