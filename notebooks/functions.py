import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from envass import qualityassurance
from datetime import datetime, timezone
import glob

def import_file(folder, date):
    file = glob.glob(folder+f"*{date}*.nc")
    dataset = xr.open_dataset(file)
    dataset["datetime"]=dataset["time"][:]
    dataset["time"] =  [datetime.timestamp(datetime.strptime(str(x.values).split(".")[0], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)) for x in dataset.time]
    return dataset

def import_nc_files(folder, date):
    """
    input: 
        folder: path where selected data is located
        date: date for data import. To select a year: date='2021' ,a month date = '202105', a day ... 
    output: 
        dataset: xarray
    """
    filelist = glob.glob(folder+f"*{date}*.nc")
    filelist.sort()
    dataset = xr.open_mfdataset(filelist, decode_times = False)
    try:
        dataset["datetime"] = pd.to_datetime(np.array(dataset["time"][:]), unit='s')
    except:
        dataset["datetime_grid"] = pd.to_datetime(np.array(dataset["time_grid"][:]), unit='s')

    return dataset

def json_converter(qa):
    for keys in qa.keys():
        try:
            if qa[keys]["simple"]["bounds"][0] == "-inf":
                qa[keys]["simple"]["bounds"][0] = -np.inf
            if qa[keys]["simple"]["bounds"][1] == "inf":
                qa[keys]["simple"]["bounds"][1] = np.inf
        except:pass
    try:
        if qa["time"]["simple"]["bounds"][1] == "now":
            qa["time"]["simple"]["bounds"][1] = datetime.now().timestamp()
        return qa
    except:
        return qa

def plot_data(df, params):
    for param in params:
        if (param in df.keys())and(param != "time"):
            fig,ax = plt.subplots()
            t = np.array(df[param])
            p = np.array(df["Press"])
            qa = np.array(df[param+"_qual"])
            p_qa = p.copy()
            p_qa[qa > 0] = np.nan
            ax.plot(t, p, color="lightgrey")
            ax.plot(t, p_qa, color="red")
            plt.title(param)
            ax.invert_yaxis()
            plt.ylabel('Pressure')
            plt.xlabel(param)
            plt.show()

def plot_grid(ds_grid, param):
    fig,ax = plt.subplots(figsize=(20,10))
    z = np.array(ds_grid[param])
    t = np.array(ds_grid["datetime_grid"])
    p = np.array(ds_grid["Press_grid"])
    x,y = np.meshgrid(t, p)
    c = ax.pcolormesh(x,y,z,cmap='jet')
    plt.title(param)
    ax.invert_yaxis()
    plt.ylabel('Pressure_grid')
    fig.colorbar(c, ax=ax)
    plt.show()
    
def quality_flags(qa, df, erase_qa=False):
    var_name = qa.keys()
    for var in var_name:
        if var in df.keys():
            if (qa[var]["advanced"]) or (qa[var]["simple"]):
                quality_assurance_all = dict(qa[var]["simple"], **qa[var]["advanced"])
                qa_arr = qualityassurance(np.array(df[var]), np.array(df["time"]), **quality_assurance_all)
                if erase_qa:
                    df[var+"_qual"].values = qa_arr
                else:
                    df[var+"_qual"].values[qa_arr] = 1
    return df

def log(str, indent=0, start=False):
    if start:
        out = "\n" + str + "\n"
        with open("log.txt", "w") as file:
            file.write(out + "\n")
    else:
        out = datetime.now().strftime("%H:%M:%S.%f") + (" " * 3 * (indent + 1)) + str
        with open("log.txt", "a") as file:
            file.write(out + "\n")
    print(out)

def update_log(quality_assurance_dict,old_quality_assurance_dict,var_name):
    var = var_name
    added_test = []
    for i in list(quality_assurance_dict[var]["advanced"].keys()):
        if i not in list(old_quality_assurance_dict[var]["advanced"].keys()):
            added_test = np.append(added_test,i)
    removed_test = []
    for j in list(old_quality_assurance_dict[var]["advanced"].keys()):
        if j not in list(quality_assurance_dict[var]["advanced"].keys()):
            removed_test = np.append(removed_test,j)
    if len(added_test)!=0:
        log(str(added_test) + " tests have been added to variable " +str(var))
    if len(removed_test)!=0:
        log(str(removed_test) + " tests have been removed to variable " +str(var))
        
def density(temperature, salinity,C_CH4=0,C_CO2=0,beta_CH4=-1.25E-3,beta_CO2=0.25E-3):
    # C_CH4 and C_CO2 must be provided in g/L
    rho = 1e3 * (
                0.9998395 + 6.7914e-5 * temperature - 9.0894e-6 * temperature ** 2 + 1.0171e-7 * temperature ** 3 -
                1.2846e-9 * temperature ** 4 + 1.1592e-11 * temperature ** 5 - 5.0125e-14 * temperature ** 6 + (
                    8.181e-4 - 3.85e-6 * temperature + 4.96e-8 * temperature ** 2) * salinity)
    # Approach: use the previous estimate of rho to calculate the next one (another option would be to use the same reference density for all estimates)
    if isinstance(C_CH4,np.ndarray) or (not C_CH4==0):
        rho=rho*(1+beta_CH4*C_CH4)
        
    if isinstance(C_CO2,np.ndarray) or (not C_CO2==0):
        rho=rho*(1+beta_CO2*C_CO2) 
        
    return rho        
	
def first_centered_differences(x, y, fill=False): 
    if x.size != y.size:
        log("first-centered differences: vectors do not have the same size")
    dy = np.full(x.size, np.nan)
    iif = np.where((np.isfinite(x)) & (np.isfinite(y)))[0]
    if iif.size == 0:
        return dy
    x0 = x[iif]
    y0 = y[iif]
    dy0 = np.full(x0.size, np.nan)
    dy0[0] = (y0[1] - y0[0]) / (x0[1] - x0[0])
    dy0[-1] = (y0[-1] - y0[-2]) / (x0[-1] - x0[-2])
    dy0[1:-1] = (y0[2:] - y0[0:-2]) / (x0[2:] - x0[0:-2])

    dy[iif] = dy0

    if fill:
        dy[0:iif[0]] = dy[iif[0]]
        dy[iif[-1] + 1:] = dy[iif[-1]]
    return dy

