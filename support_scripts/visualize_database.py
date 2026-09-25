import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
from datetime import datetime, timezone
import cmocean
import xarray as xr
from scripts.functions import read_netCDF_xr
import mplcursors

def load_level3_nc():
    #database_file = "../data/ctd/Level3/Combined/L3_comb.nc"
    database_file = "/storage/lakekivu/1D_Model/WP_workspaces/WP2/db_workspace/database_runs/full_database/L3_comb.nc"
    data_CTD=read_netCDF_xr(database_file)
    tnum=data_CTD["time"].values
    ds = xr.decode_cf(xr.Dataset({"time": ("time", data_CTD.time.data,{"units":"seconds since 1970-01-01"})}))
    data_CTD["time"]=ds["time"].data
    return data_CTD

def plot_contour_nc(data_CTD, par="Temperature", dmin=0):

    ind_deepprof = np.where(
        data_CTD["max_depth"].values >= dmin
    )[0]

    if par == "Temperature":
        variable = "Temp"
        cmap = cmocean.cm.thermal
        cbar_label = r"$T$ [$^\circ$C]"

    elif par == "Salinity":
        variable = "SALIN"
        cmap = cmocean.cm.haline
        cbar_label = r"$S$ [g kg$^{-1}$]"

    elif par == "Density":
        variable = "rho"
        cmap = cmocean.cm.dense
        cbar_label = r"$\rho$ [kg m$^{-3}$]"

    else:
        raise ValueError(f"Unknown parameter: {par}")

    time = data_CTD["time"].values[ind_deepprof]
    depth = data_CTD["depth_interp"].values

    x, y = np.meshgrid(time, depth)

    z = data_CTD[variable].values[:, ind_deepprof]

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    mesh = ax.pcolormesh(
        x,
        y,
        z,
        cmap=cmap,
        shading="auto"
    )

    cb = fig.colorbar(mesh, ax=ax)
    cb.set_label(cbar_label)

    ax.set_xlabel("Date")
    ax.set_ylabel("Depth [m]")

    ax.invert_yaxis()

    #     # --------------------------------------------------
#     # Interactive cursor
#     # --------------------------------------------------
#     cursor = mplcursors.cursor(
#         mesh,
#         hover=True
#     )

#     @cursor.connect("add")
#     def on_add(sel):

#         # Position of mouse in data coordinates
#         x_mouse = sel.target[0]
#         y_mouse = sel.target[1]

#         # Find closest time
#         time_index = np.argmin(
#             np.abs(
#                 time.astype("datetime64[ns]")
#                 - np.datetime64(x_mouse)
#             )
#         )

#         # Find closest depth
#         depth_index = np.argmin(
#             np.abs(depth - y_mouse)
#         )

#         value = z[
#             depth_index,
#             time_index
#         ]

#         date_value = time[
#             time_index
#         ]

#         # Format date
#         date_string = np.datetime_as_string(
#             date_value,
#             unit="D"
#         )

#         sel.annotation.set_text(
#             f"Date: {date_string}\n"
#             f"Depth: {depth[depth_index]:.1f} m\n"
#             f"{par}: {value:.3f}"
#         )

    return fig, ax


# FUNCTION VI.1
def plot_contour_nc_old(data_CTD, par=None, dmin=0): # only for tests

    ind_deepprof=np.where(data_CTD['max_depth'].values>=dmin)[0]

    fig,ax = plt.subplots(2,1,figsize=(8,6),sharey=True,sharex=True)
    if "time" in data_CTD.coords:
        x,y = np.meshgrid(data_CTD["time"][ind_deepprof],data_CTD["depth_interp"])
    #elif "month" in data_CTD.coords:
        #x,y = np.meshgrid(data_CTD["month"][ind_deepprof],data_CTD["depth_interp"])
    ptemp = ax[0].pcolormesh(x,y,data_CTD["Temp"][:,ind_deepprof],cmap=cmocean.cm.thermal)
    cb=fig.colorbar(ptemp, ax=ax[0])
    cb.set_label('$T$ [$^{\\circ}$C]')
    ax[0].set_ylabel('Depth [m]')
    ylimval=ax[0].get_ylim()
    ax[0].set_ylim(ylimval)
    #for kprof in np.arange(len(data_CTD.time)):
        #ax[0].plot(np.full(2,data_CTD.time[kprof]),np.array([ylimval[1]-10,ylimval[1]]),'-r',linewidth=0.5)

    psal = ax[1].pcolormesh(x,y,data_CTD["SALIN"][:,ind_deepprof],cmap=cmocean.cm.haline)
    cb=fig.colorbar(psal, ax=ax[1])
    cb.set_label('$S$ [g kg$^{-1}$]')
    ax[1].set_ylabel('Depth [m]')

    prho = ax[2].pcolormesh(x,y,data_CTD["rho"][:,ind_deepprof],cmap=cmocean.cm.dense)
    cb=fig.colorbar(prho, ax=ax[2])
    cb.set_label('$\\rho$ [kg m$^{-3}$]')
    ax[2].set_ylabel('Depth [m]')

    ax[0].invert_yaxis()