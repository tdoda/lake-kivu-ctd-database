import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
from datetime import datetime, timezone
import cmocean
import xarray as xr
from scripts.functions import read_netCDF_xr
import matplotlib.dates as mdates

#import mplcursors
from pathlib import Path

def load_level3_nc(database_file):
    #database_file = "../data/ctd/Level3/Combined/L3_comb.nc"
    #database_file = "/storage/lakekivu/1D_Model/WP_workspaces/WP2/db_workspace/database_runs/full_database/L3_comb.nc"
    data_CTD=read_netCDF_xr(database_file)
    #tnum=data_CTD["time"].values
    ds = xr.decode_cf(xr.Dataset({"time": ("time", data_CTD.time.data,{"units":"seconds since 1970-01-01"})}))
    data_CTD["time"]=ds["time"].data
    return data_CTD


def get_database_date_range(data_CTD):

    time = data_CTD["time"].values

    min_date = np.datetime_as_string(
        time.min(),
        unit="D"
    )

    max_date = np.datetime_as_string(
        time.max(),
        unit="D"
    )

    return min_date, max_date

def filter_visualization_data(
    data_CTD,
    start_date,
    end_date,
    z_below):

    time = data_CTD["time"]

    mask_date = (
        (time >= np.datetime64(start_date)) &
        (time <= np.datetime64(end_date))
    )
    mask_depth = (
        data_CTD["max_depth"] >= z_below
    )
    mask = mask_date & mask_depth
    data_filtered = data_CTD.isel(time=mask)

    #def prepare_plot_data(ds):

    """Reduce the vertical resolution for GUI visualization."""
    # Original: 0.2 m resolution starting at 0 m
    # Visualization: 2 m resolution starting at 2 m
    ds_plot = data_filtered.isel(depth_interp=slice(10, None, 10))

    return ds_plot

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

    elif par == "Conductivity":

        variable = "Cond20"
        cmap = cmocean.cm.speed
        cbar_label = r"$\mathrm{Cond}_{20}$ [mS cm$^{-1}$]"

    else:

        raise ValueError(
            f"Unknown parameter: {par}"
        )

    time = data_CTD["time"].values[ind_deepprof]

    depth = data_CTD["depth_interp"].values

    x, y = np.meshgrid(time, depth)

    z = data_CTD[variable].values[:, ind_deepprof]

    fig, ax = plt.subplots()

    mesh = ax.pcolormesh(
        x,
        y,
        z,
        cmap=cmap,
        shading="auto"
    )

    cb = fig.colorbar(
        mesh,
        ax=ax
    )

    cb.set_label(cbar_label)

    ax.set_xlabel("Date")
    ax.set_ylabel("Depth [m]")

    ax.invert_yaxis()

    # --------------------------------------------------
    # Interactive cursor
    # --------------------------------------------------

    annotation = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        bbox=dict(
            boxstyle="round",
            fc="white",
            alpha=0.9
        )
        #arrowprops=dict(
            #arrowstyle="->"
        #)
    )

    annotation.set_visible(False)


    def on_mouse_move(event):

        if event.inaxes != ax:
            annotation.set_visible(False)
            fig.canvas.draw_idle()
            return

        if event.xdata is None or event.ydata is None:
            return

        x_mouse = event.xdata
        y_mouse = event.ydata

        # Convert mouse x-position back to datetime
        mouse_date = mdates.num2date(x_mouse)

        mouse_date = np.datetime64(
            mouse_date.replace(tzinfo=None)
        )

        # Find closest time
        time_index = np.argmin(
            np.abs(
                time.astype("datetime64[ns]")
                - mouse_date
            )
        )

        # Find closest depth
        depth_index = np.argmin(
            np.abs(
                depth - y_mouse
            )
        )

        value = z[
            depth_index,
            time_index
        ]

        date_value = time[
            time_index
        ]

        date_string = np.datetime_as_string(
            date_value,
            unit="D"
        )

        # Position annotation at selected point
        annotation.xy = (
            date_value,
            depth[depth_index]
        )

        annotation.set_text(
            f"Date: {date_string}\n"
            f"Depth: {depth[depth_index]:.1f}\n"
            f"{par}: {value:.3f}"
        )

        annotation.set_visible(True)

        fig.canvas.draw_idle()


    fig.canvas.mpl_connect(
        "motion_notify_event",
        on_mouse_move
    )

    return fig, ax


def plot_contour_nc_new(data_CTD, par="Temperature", dmin=0):

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

    elif par == "Conductivity":
        variable = "Cond20"
        cmap = cmocean.cm.speed
        cbar_label = r"$\mathrm{Cond}_{20}$ [mS cm$^{-1}$]"

    else:
        raise ValueError(
            f"Unknown parameter: {par}"
        )

    time = data_CTD["time"].values[ind_deepprof]
    depth = data_CTD["depth_interp"].values

    x, y = np.meshgrid(time, depth)

    z = data_CTD[variable].values[:, ind_deepprof]

    fig, ax = plt.subplots()

    mesh = ax.pcolormesh(
        x,
        y,
        z,
        cmap=cmap,
        shading="auto"
    )

    cb = fig.colorbar(
        mesh,
        ax=ax
    )

    cb.set_label(cbar_label)

    ax.set_xlabel("Date")
    ax.set_ylabel("Depth [m]")
    ax.invert_yaxis()

    fig.tight_layout()

    return fig, ax

# def plot_contour_nc(data_CTD, par="Temperature", dmin=0):

#     ind_deepprof = np.where(
#         data_CTD["max_depth"].values >= dmin
#     )[0]

#     if par == "Temperature":

#         variable = "Temp"
#         cmap = cmocean.cm.thermal
#         cbar_label = r"$T$ [$^\circ$C]"

#     elif par == "Salinity":

#         variable = "SALIN"
#         cmap = cmocean.cm.haline
#         cbar_label = r"$S$ [g kg$^{-1}$]"

#     elif par == "Density":

#         variable = "rho"
#         cmap = cmocean.cm.dense
#         cbar_label = r"$\rho$ [kg m$^{-3}$]"

#     else:
#         raise ValueError(f"Unknown parameter: {par}")

#     time = data_CTD["time"].values[ind_deepprof]
#     depth = data_CTD["depth_interp"].values

#     x, y = np.meshgrid(time, depth)

#     z = data_CTD[variable].values[:, ind_deepprof]

#     fig, ax = plt.subplots(
#         figsize=(10, 6)
#     )

#     mesh = ax.pcolormesh(
#         x,
#         y,
#         z,
#         cmap=cmap,
#         shading="auto"
#     )

#     cb = fig.colorbar(mesh, ax=ax)
#     cb.set_label(cbar_label)

#     ax.set_xlabel("Date")
#     ax.set_ylabel("Depth [m]")

#     ax.invert_yaxis()

#     #     # --------------------------------------------------
# #     # Interactive cursor
# #     # --------------------------------------------------
# #     cursor = mplcursors.cursor(
# #         mesh,
# #         hover=True
# #     )

# #     @cursor.connect("add")
# #     def on_add(sel):

# #         # Position of mouse in data coordinates
# #         x_mouse = sel.target[0]
# #         y_mouse = sel.target[1]

# #         # Find closest time
# #         time_index = np.argmin(
# #             np.abs(
# #                 time.astype("datetime64[ns]")
# #                 - np.datetime64(x_mouse)
# #             )
# #         )

# #         # Find closest depth
# #         depth_index = np.argmin(
# #             np.abs(depth - y_mouse)
# #         )

# #         value = z[
# #             depth_index,
# #             time_index
# #         ]

# #         date_value = time[
# #             time_index
# #         ]

# #         # Format date
# #         date_string = np.datetime_as_string(
# #             date_value,
# #             unit="D"
# #         )

# #         sel.annotation.set_text(
# #             f"Date: {date_string}\n"
# #             f"Depth: {depth[depth_index]:.1f} m\n"
# #             f"{par}: {value:.3f}"
# #         )

#     return fig, ax


# FUNCTION VI.1
def export_variable_to_csv(
    data_CTD,
    variable,
    start_date,
    end_date,
    z_below,
    project_dir,
    source="Comb"
):
    """
    Export one CTD variable to CSV.

    The CSV contains one row per CTD profile.

    Columns:
        datetime
        latitude
        longitude
        dist_GEF
        min_depth
        max_depth
        depth levels

    The original vertical resolution of data_CTD is preserved.
    """

    # --------------------------------------------------------
    # 1. Filter profiles
    # --------------------------------------------------------

    time = data_CTD["time"]

    mask_date = (
        (time >= np.datetime64(start_date)) &
        (time <= np.datetime64(end_date))
    )

    mask_depth = (
        data_CTD["max_depth"] >= z_below
    )

    mask = mask_date & mask_depth

    data_export = data_CTD.isel(
        time=mask
    )

    # --------------------------------------------------------
    # 2. Check that profiles were found
    # --------------------------------------------------------

    if data_export.sizes["time"] == 0:
        raise ValueError(
            "No CTD profiles match the selected filters."
        )

    # --------------------------------------------------------
    # 3. Check that variable exists
    # --------------------------------------------------------

    if variable not in data_export:
        raise ValueError(
            f"Variable '{variable}' was not found in the database."
        )

    # --------------------------------------------------------
    # 4. Create output folder
    # --------------------------------------------------------
    output_folder = os.path.join(
        project_dir,
        "export"
    )
    os.makedirs(
        output_folder,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 5. Extract profile metadata
    # --------------------------------------------------------

    datetime_values = data_export["time"].values

    latitude = data_export["latitude"].values
    longitude = data_export["longitude"].values
    dist_GEF = data_export["dist_GEF"].values
    min_depth = data_export["min_depth"].values
    max_depth = data_export["max_depth"].values

    # --------------------------------------------------------
    # 6. Extract depth coordinate
    # --------------------------------------------------------

    depths = data_export["depth_interp"].values

    # --------------------------------------------------------
    # 7. Extract variable
    # --------------------------------------------------------

    values = data_export[variable].values

    # NetCDF structure:
    #
    #     depth × time
    #
    # CSV structure:
    #
    #     time × depth
    #
    values = values.T

    # --------------------------------------------------------
    # 8. Create DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(
        values,
        columns=depths
    )

    # --------------------------------------------------------
    # 9. Add profile metadata
    # --------------------------------------------------------

    df.insert(
        0,
        "datetime",
        datetime_values
    )

    df.insert(
        1,
        "latitude",
        latitude
    )

    df.insert(
        2,
        "longitude",
        longitude
    )

    df.insert(
        3,
        "dist_GEF",
        dist_GEF
    )

    df.insert(
        4,
        "min_depth",
        min_depth
    )

    df.insert(
        5,
        "max_depth",
        max_depth
    )

    # --------------------------------------------------------
    # 10. Format depth column names
    # --------------------------------------------------------

    fixed_columns = [
        "datetime",
        "latitude",
        "longitude",
        "dist_GEF",
        "min_depth",
        "max_depth"
    ]

    df.columns = [
        column
        if column in fixed_columns
        else f"{float(column):.1f}"
        for column in df.columns
    ]

    # --------------------------------------------------------
    # 11. Get variable unit
    # --------------------------------------------------------

    unit = data_CTD[variable].attrs.get(
        "units",
        ""
    )

    unit = unit.replace("/", "_")

    # --------------------------------------------------------
    # 12. Create filename
    # --------------------------------------------------------

    if unit:

        filename = (
            f"{source}_{variable}_"
            f"{start_date}_{end_date}_"
            f"{z_below:g}_{unit}.csv"
        )

    else:

        filename = (
            f"{source}_{variable}_"
            f"{start_date}_{end_date}_"
            f"z{z_below:g}.csv"
        )

    out_file = os.path.join(
        output_folder,
        filename
    )

    # --------------------------------------------------------
    # 13. Export
    # --------------------------------------------------------

    df.to_csv(
        out_file,
        index=False,
        float_format="%.4f"
    )

    return out_file
