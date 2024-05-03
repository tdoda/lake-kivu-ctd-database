import os
import json
import math
import numpy as np
import pandas as pd
import gsw
import seawater as sw
from shutil import copyfile
from envass import qualityassurance
from datetime import datetime, timedelta
import time
from scipy.ndimage import uniform_filter1d
from sklearn.linear_model import LinearRegression
from scipy.optimize import curve_fit
import netCDF4



def copyFiles(outfolder, infolder):
    filelist = []
    for path, subdirs, files in os.walk(infolder):
        for name in files:
            filelist.append(os.path.join(path, name))

    copied = []
    for file in filelist:
        if ".TOB" in file and not os.path.isfile(os.path.join(outfolder, os.path.basename(file))):
            path_arr = os.path.basename(file).split(".")
            new_file = "{}__{}.{}".format(os.path.basename(os.path.dirname(file)), path_arr[0], path_arr[1])
            copyfile(file, os.path.join(outfolder, new_file))
            copied.append(file)
    return copied


def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return True


def check_valid_profile(data, value):
    if float(np.nanmax(data)) > float(value):
        return True
    else:
        return False


def strip_metadata(metadata):
    return metadata.replace(" ", "").split(":")[1]


def fixed_grid_resample_guide(data, grid):
    resample = []
    for g in grid:
        for j in range(len(data)):
            if data[j] > g or j >= len(data) - 1:
                resample.append({"index": False})
                break
            elif data[j] <= g < data[j + 1]:
                itp = (g - data[j]) / (data[j + 1] - data[j])
                resample.append({"index": j, "interpolation": itp})
                break
    return resample


def resample(guide, data):
    out = []
    for i in range(len(guide) - 1):
        if not guide[i]["index"]:
            out.append(np.nan)
        else:
            value = ((data[guide[i]["index"] + 1] - data[guide[i]["index"]]) * guide[i]["interpolation"]) + data[guide[i]["index"]]
            out.append(value)
    out.append(np.nan)
    return out


def index_of_max(arr):
    return np.argmax(np.array(arr))


def position_in_array(arr, value):
    for i in range(len(arr)):
        if value < arr[i]:
            return i
    return len(arr)


def round_to_days(dt, n):
    day = math.floor(dt.day / n)*n
    if day < 10:
        return "0" + str(day)
    else:
        return str(day)


def advanced_quality_flags(df, json_path="quality_assurance.json"):
    """
        input :
            - df is a dataframe of level 1B where basic check have been performed
            - json path: path for the advanced quality check json file, produced by the jupyter notebook
        output:
            - dictionnary where the dataframe is stored with updated advanced quality checks
        """
    quality_assurance_dict = json.load(open(json_path))
    var_name = quality_assurance_dict.keys()
    advanced_df = df.copy()
    for var in var_name:
        if quality_assurance_dict[var]:
            if var in advanced_df.keys(): 
                qa = qualityassurance(np.array(df[var]), np.array(df["time"]), **quality_assurance_dict[var]["advanced"])
                advanced_df[var + "_qual"].values[np.array(qa, dtype=bool)] = 1
    return advanced_df


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


def error(str):
    out = datetime.now().strftime("%H:%M:%S.%f") + "   ERROR: " + str
    with open("log.txt", "a") as file:
        file.write(out + "\n")
    raise ValueError(str)


def find_closest_index(arr, value):
    return min(range(len(arr)), key=lambda i: abs(arr[i] - value))


def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return True


def isnt_number(n):
    try:
        float(n)
    except ValueError:
        return True
    else:
        return False

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

def mask_single_data(data, mask):
    try:
        idx = mask > 0
        data = data.astype(float)
        data[idx] = np.nan
        return data
    except:
        print("Masking failed")
        return data

        
def rename_duplicates(arr):
    out = []
    d = {}

    for i in arr:
        d.setdefault(i, -1)
        d[i] += 1

        if d[i] >= 1:
            out.append('%s%d' % (i, d[i]))
        else:
            out.append(i)
    return out



def check_variable(variable, unit, columns, units):
    if variable in columns:
        for i in range(len(columns)):
            if variable == columns[i]:
                break
        if units[i] in unit: 
            return True
        else:
            log("{} needs unit [{}] but has unit [{}]".format(variable, unit, units[i]))
            return False
    else:
        return False


def qa_std_moving(variable, xdata=np.array([]), window_size=15, factor=3, prior_flags=False):
   """
   Indicate outliers values based on std applied to moving average.
   Parameters:
       variable (np.array): Data array to which to apply the quality assurance
       xdata (np.array): x-values used to resample the data (if not specified, data is not resample)
       window_size (np.int): window size of data
       factor (int): number n such that values higher than n*std are considered as outliers
       prior_flags (np.array): An array of bools where True means non-trusted data
   Returns:
       flags (np.array): An array of bools where True means non-trusted data for this outlier dectection
   """
   if isinstance(prior_flags,np.ndarray): # Boolean array provided
       flags = prior_flags
   else: # No boolean array provided
       flags=np.full(variable.shape,False)

   if len(variable) < window_size:
       print("ERROR! Window size is larger than array length.")
   else:
        # if ~np.any(xdata):
        #     xdata:np.arange(len(variable))
        #Interpolate data at constant intervals
        # xinterp=np.linspace(np.min(xdata),np.max(xdata),len(variable))
        # indsort=np.argsort(xdata)
        # yinterp=np.interp(xinterp, xdata[indsort], variable[indsort])
        # movmean=np.interp(xdata,xinterp,uniform_filter1d(yinterp,size=window_size))
        movmean=uniform_filter1d(variable,size=window_size)
        noise_data=abs(variable-movmean)
        mask_std=noise_data>factor*np.std(noise_data)
        flags=np.logical_or(flags,mask_std)
   return flags

def regression_oneline(x,y,forced_point=(np.nan,np.nan)):
    # For 1D array
          
    if np.isnan(forced_point[0]) or np.isnan(forced_point[1]):        
        model=LinearRegression().fit(x[~np.isnan(y)].reshape(-1,1),y[~np.isnan(y)])
        R2=model.score(x[~np.isnan(y)].reshape(-1,1),y[~np.isnan(y)])
        pfit=[model.coef_[0],model.intercept_]
    else:
        model=LinearRegression(fit_intercept=False).fit((x[~np.isnan(y)]-forced_point[0]).reshape(-1,1),y[~np.isnan(y)]-forced_point[1]) 
        R2=model.score((x[~np.isnan(y)]-forced_point[0]).reshape(-1,1),y[~np.isnan(y)]-forced_point[1])
        pfit=[model.coef_[0],forced_point[1]-model.coef_[0]*forced_point[0]]
    yfit=np.polyval(pfit,x)
    
    # Standard error of the slope and intercept
    se_slope = np.sqrt(np.sum((y[~np.isnan(y)]-yfit[~np.isnan(y)])**2)/((len(x[~np.isnan(y)])-2)*np.sum((x[~np.isnan(y)]-np.mean(x[~np.isnan(y)]))**2)))
    se_intercept=se_slope*np.sqrt(1/len(x[~np.isnan(y)])*np.sum(x[~np.isnan(y)]**2))
    SE=[se_slope,se_intercept]

    return pfit, yfit, R2, SE

def regression_period(tval,zval,t_extract,interceptval=np.full(2,np.nan)):
    zchem_periods=[zval[tval<t_extract],zval[tval>=t_extract]]
    tchem_periods=[tval[tval<t_extract].reshape(-1,1),tval[tval>=t_extract].reshape(-1,1)]
    model=[None]*2
    R2=[None]*2
    pfit=[None]*2
    zfit=[None]*2
    for i in [0,1]:
        if np.isnan(interceptval[i]):
            model[i]=LinearRegression().fit(tchem_periods[i][~np.isnan(zchem_periods[i])],zchem_periods[i][~np.isnan(zchem_periods[i])])
            R2[i]=model[i].score(tchem_periods[i][~np.isnan(zchem_periods[i])],zchem_periods[i][~np.isnan(zchem_periods[i])])
            pfit[i]=[model[i].coef_[0],model[i].intercept_]
            zfit[i]=np.polyval(pfit[i],tchem_periods[i])
        else:
            model[i]=LinearRegression(fit_intercept=False).fit(tchem_periods[i][~np.isnan(zchem_periods[i])],zchem_periods[i][~np.isnan(zchem_periods[i])]-interceptval) 
            R2[i]=model[i].score(tchem_periods[i][~np.isnan(zchem_periods[i])],zchem_periods[i][~np.isnan(zchem_periods[i])]-interceptval)
            pfit[i]=[model[i].coef_[0],interceptval]
            zfit[i]=np.polyval(pfit[i],tchem_periods[i])
    
    return pfit, tchem_periods, zfit, R2

def regression_period_intersect(tval,zval,t_extract, param0):
    x0=t_extract
    # Force intersection between two lines    
    def two_linear_models(x, a1, b1, a2):
        #nonlocal x0
        # Define the piecewise linear model
        y = np.where(x < x0, a1 * x + b1, a2 * x + x0*(a1-a2)+b1)
        return y
    params,pcov = curve_fit(two_linear_models, tval[~np.isnan(zval)], zval[~np.isnan(zval)], p0=param0)
    zfit=two_linear_models(tval,params[0],params[1],params[2])
    R2=[1-np.nansum((zval[tval<t_extract]-zfit[tval<t_extract])**2)/np.nansum((zval[tval<t_extract]-np.nanmean(zval[tval<t_extract]))**2),
        1-np.nansum((zval[tval>t_extract]-zfit[tval>t_extract])**2)/np.nansum((zval[tval>t_extract]-np.nanmean(zval[tval>t_extract]))**2)]
    return [[params[0],params[1]], [params[2],x0*(params[0]-params[2])+params[1]]], zfit, R2, pcov


def divide_paths(x,y,maxdist=1e-5):
    x_corr=[]
    y_corr=[]
    distval=(x[1:]-x[:-1])**2+(y[1:]-y[:-1])**2
    indsegments_start=np.concatenate(([0],np.where(distval>maxdist)[0]+1),axis=0)
    indsegments_end=np.concatenate((np.where(distval>maxdist)[0],[len(x)-1]),axis=0)
    
    for kseg in range(len(indsegments_start)):
        x_corr.append(x[indsegments_start[kseg]:indsegments_end[kseg]])
        y_corr.append(y[indsegments_start[kseg]:indsegments_end[kseg]])
    
    return x_corr, y_corr

def movmean(X,windowsize,axis=0):
    """Function movmean

    Computes the moving average of an array centered at the given index.

    Inputs:
        X (numpy array (m,n) of floats): array to average
        windowsize (int): size of the averaging window
        axis (int): index of the axis along which the averaging is applied
        
    Outputs:
        X_smooth (numpy array (m,n) of floats): smoothed array
    """

    if len(X.shape)==1:
        X=np.expand_dims(X,axis=1)
    if axis==1:
        X=X.transpose()
    X_smooth=np.full(X.shape,np.nan)
    for k in range(X.shape[1]): 
        df=pd.DataFrame({'val':X[:,k]})
        X_smooth[:,k]=df.rolling(windowsize,center=True).mean().values[:,0]
    if axis==1:
        X_smooth=X_smooth.transpose()
    return X_smooth

def fit_rho(depthval,rhoval,rho_top,rho_bot,z_bounds,param_ini): 
    # All input arguments are numpy arrays
    zmin=z_bounds[0]
    zmax=z_bounds[1]
    if len(rhoval.shape)==1:
        rhoval=np.expand_dims(rhoval,axis=1)
    if not isinstance(rho_top,np.ndarray):
        rho_top=np.array([rho_top])
    if not isinstance(rho_bot,np.ndarray):
        rho_bot=np.array([rho_bot])
    nprof=rhoval.shape[1]
    if len(rho_bot)!=nprof or len(rho_top)!=nprof:
        raise Exception('Wrong dimension of upper and lower densities')
    zchemfit=np.full((nprof,),np.nan)
    deltafit=np.full((nprof,),np.nan)
    log("Fitting density profile",indent=2)
    for kt in range(nprof):
        # Fitting function:
        def densfunc(z,zchem,delta): 
            # z>0 downward
            return rho_top[kt]+(rho_bot[kt]-rho_top[kt])/2*(np.tanh((z-zchem)/delta)+1)
        keepdepth=np.logical_and.reduce((~np.isnan(rhoval[:,kt]),depthval>=zmin,depthval<=zmax))
        param,pcov,infodict,_,_= curve_fit(densfunc, depthval[keepdepth],rhoval[keepdepth,kt],p0=param_ini,full_output=True)
        zchemfit[kt]=param[0]
        deltafit[kt]=param[1]
    return zchemfit, deltafit, pcov, infodict

def densprofile(z,delta,zchem,rho_top,rho_bot): 
    # z>0 downward
    return rho_top+(rho_bot-rho_top)/2*(np.tanh((z-zchem)/delta)+1)

def compute_hypso(depthval,dA,dz):
    # depth val: numerical array with grid of POSITIVE depth values [m]
    # dA: surface area of a grid cell [m^2]
    # dz: vertical resolution for the output [m]
    
    
    hypso_z=np.arange(0,np.nanmax(depthval),dz)
    hypso_A=np.array([np.nan]*len(hypso_z))
    for k in range(len(hypso_z)):
        hypso_A[k]=np.nansum(depthval>=hypso_z[k])*dA # [m^2]
    
    return hypso_z, hypso_A

def compute_balance(database,indprof,zval,Aval,Cp=4.18,Sbot=5.5):
    
    H=np.full((len(zval),len(indprof)),np.nan)
    S=np.full((len(zval),len(indprof)),np.nan)
    M=np.full((len(zval),len(indprof)),np.nan)
    
    for kz in range(len(zval)-1):
        tempval=np.nanmean(database.Temp.values[np.logical_and(database.depth_interp>=zval[kz],database.depth_interp<zval[kz+1])][:,indprof],axis=0)
        salval=np.nanmean(database.SALIN.values[np.logical_and(database.depth_interp>=zval[kz],database.depth_interp<zval[kz+1])][:,indprof],axis=0)
        densval=np.nanmean(database.rho.values[np.logical_and(database.depth_interp>=zval[kz],database.depth_interp<zval[kz+1])][:,indprof],axis=0)
        
        H[kz,:]=tempval*densval*Cp*0.5*(Aval[kz]+Aval[kz+1])*(zval[kz+1]-zval[kz]) # [J]
        S[kz,:]=salval*densval*0.5*(Aval[kz]+Aval[kz+1])*(zval[kz+1]-zval[kz])/1000 # [kg salt]
        M[kz,:]=densval*0.5*(Aval[kz]+Aval[kz+1])*(zval[kz+1]-zval[kz]) # [kg water]   
    
    return H, S, M

def compute_N2(zval,rhoval,windowsize=10,g=9.81):
    # zval increases downward
    
    zval=zval.reshape(-1,1)
    rho_smooth=movmean(rhoval,windowsize,axis=0)
     
    rho0=np.nanmean(rho_smooth,axis=0)
    N2=np.full(rho_smooth.shape,np.nan)
    N2[1:,:]=1/rho0*np.diff(rho_smooth,axis=0)/np.diff(zval,axis=0)*g
    
    return N2

def compute_Sc(zval,rhoval,min_depth_profiles,max_depth_profiles,hypso_z,hypso_A,zmin=1,zmax=300,g=9.81,layer_specific=False):
    # zval increases downward
    zval=zval.reshape(-1,1)
    
    if layer_specific: # Compute Sc by only using the data from the layer defined by zmin & zmax
        ind_keep=np.where(np.logical_and(zval>zmin,zval<zmax))[0]
        zval=zval[ind_keep]-zmin #z=0 at zmin
        hypso_z=hypso_z-zmin
        rhoval=rhoval[ind_keep,:]
    
    rhomean=np.nanmean(rhoval,axis=0)
    Aval=np.interp(zval,hypso_z,hypso_A)
    zv=np.trapz(zval*Aval,zval,axis=0)/np.trapz(Aval,zval,axis=0)
    Sc_Read=np.array([np.nan]*rhoval.shape[1]) # J
    Sc_Imb=np.array([np.nan]*rhoval.shape[1]) # J
    for kt in range(len(Sc_Read)):
        if max_depth_profiles[kt]>=zmax and min_depth_profiles[kt]<=zmin: # Profile is long enough
            if layer_specific:
                valkeep=~np.isnan(rhoval[:,kt])
            else:
                valkeep=np.logical_and(~np.isnan(rhoval[:,kt]),np.logical_and(zval[:,0]>=zmin,zval[:,0]<=zmax))
            Sc_Read[kt]=g*np.trapz((zval[valkeep][:,0]-zv)*rhoval[valkeep,kt]*Aval[valkeep][:,0],zval[valkeep][:,0],axis=0)
            Sc_Imb[kt]=g*np.trapz((zval[valkeep][:,0]-zv)*(rhoval[valkeep,kt]-rhomean[kt])*Aval[valkeep][:,0],zval[valkeep][:,0],axis=0)
    
    return Sc_Read, Sc_Imb 

def sort_paths(x,y,maxdist=0.01):
    # x, y: 1D numpy arrays
    # returns x_corr and y_corr: lists of numpy 1D arrays (one element for each contour)
    breakpoint()
    x_corr=[]
    y_corr=[]
    distval=(x[1:]-x[:-1])**2+(y[1:]-y[:-1])**2
    indsegments_start=np.concatenate(([0],np.where(distval>maxdist)[0]+1),axis=0)
    indsegments_end=np.concatenate((np.where(distval>maxdist)[0],[len(x)-1]),axis=0)
    
    if len(indsegments_start)==1: # No jump
        print('Already sorted!')
        x_corr=[x]
        y_corr=[y]
        return x_corr, y_corr
    
    indbefore=np.full(len(indsegments_start),np.nan) # Index of the segment preceding the current location
    indseg_all=np.arange(len(indsegments_start))
    
    for kseg in indseg_all:   
        ind_other=np.delete(indseg_all,kseg)
        dist_other=(x[indsegments_start[kseg]]-x[indsegments_end[ind_other]])**2+(y[indsegments_start[kseg]]-y[indsegments_end[ind_other]])**2
        ind_close=np.nanargmin(dist_other) # Put current segment after this one
        if dist_other[ind_close]>maxdist: #Still jump: move the segment to the beginning
            indbefore[kseg]=-1
        else:
            indbefore[kseg]=ind_other[ind_close]

    if -1 not in indbefore:
        print('No clear starting point (loop)')
        indsort=np.full(len(indbefore),np.nan) # Indices of the segments in the right order
        indsort[0]=indbefore[0]
    else:
        ind_isolated=np.where([i not in indbefore for i in indseg_all[np.where(indbefore==-1)[0]]])[0]
        # Add segments with only one point:
        ind_isolated=np.concatenate((ind_isolated,np.where(indsegments_start==indsegments_end)[0]))
        #if np.any(ind_isolated):
        if len(ind_isolated)>=1:
            #indseg_all[np.where(indbefore==-1)[0]] not in indbefore: # Isolated segment
            print('Isolated segments!')
            for k in range(len(ind_isolated)):
                x_corr.append(x[indsegments_start[int(ind_isolated[k])]:indsegments_end[int(ind_isolated[k])]])
                y_corr.append(y[indsegments_start[int(ind_isolated[k])]:indsegments_end[int(ind_isolated[k])]])
            indkeep=np.delete(indbefore,np.where(indbefore==-1)[0])
            if np.any(indkeep):
                indsort=np.full(len(indkeep),np.nan) # Indices of the segments in the right order
                indsort[0]=indkeep[0]
            else: # No segment left
                return x_corr, y_corr
        else: # No isolated segment
            indsort=np.full(len(indbefore),np.nan) # Indices of the segments in the right order
            indsort[0]=np.where(indbefore==-1)[0]
            
            
    #print(indbefore)
    for k in np.arange(1,len(indsort),1):
        indbef_val=np.where(indbefore==indsort[k-1])[0]
        if isinstance(indbef_val,np.ndarray) and len(indbef_val)>1:
            breakpoint()
            raise Exception('Several segments are repeated')
        else:
            indsort[k]=indbef_val
    #print(indsort)
    xval_corr=x[indsegments_start[int(indsort[0])]:indsegments_end[int(indsort[0])]]
    yval_corr=y[indsegments_start[int(indsort[0])]:indsegments_end[int(indsort[0])]]
    for k in np.arange(1,len(indsort),1):
        xval_corr=np.concatenate((xval_corr,x[indsegments_start[int(indsort[k])]:indsegments_end[int(indsort[k])]]))
        yval_corr=np.concatenate((yval_corr,y[indsegments_start[int(indsort[k])]:indsegments_end[int(indsort[k])]]))
    
    x_corr.append(xval_corr)
    y_corr.append(yval_corr)
    
    return x_corr, y_corr

def extract_dict_netcdf(nc):
    # Returns the four disctionaries used to create the netCDF file (generat attributes, dimensions, variables and data)
    
    # General attributes
    gen_att_nc=nc.__dict__
    
    # Dimensions
    dim_names=list(nc.dimensions)
    dim_nc=dict()
    for kdim in range(len(dim_names)):
        dim_nc[dim_names[kdim]]={'dim_name':dim_names[kdim],'dim_size': None}
        
    # Variables
    var_names=list(nc.variables)
    var_nc=dict()
    for kvar in range(len(var_names)):
        var_nc[var_names[kvar]]={'var_name': var_names[kvar], 
                                 'dim': nc.variables[var_names[kvar]].dimensions, 
                                 'unit': nc.variables['time'].units, 
                                 'longname': nc.variables['time'].long_name}
    
    
    # Data
    data_nc=extract_data_netcdf(nc)
    
    
    return gen_att_nc,dim_nc,var_nc,data_nc

def extract_data_netcdf(nc):
    # Returns the variables of a netcdf file as a dictionary
    varnames=list(nc.variables)
    data=dict()
    
    for kvar in range(len(varnames)):
        data[varnames[kvar]]=nc.variables[varnames[kvar]][:].data
    return data

def select_data(data,var,dim_selected,ind_selected):
    """
    Select data according to boolean array along a specific dimension
    
    Inputs:
        data: dictionary with data of each variable
        var: dictionary with attributes of each variable
        dim_selected (string): name of dimension along which data must be selected
        ind_selected: numpy array with indices of values to select along the selected dimension
    
    """
    
    data_selected=data.copy()
    
    for varname,var_dict in var.items():
        if dim_selected in var_dict["dim"]: # One of the dimensions of the variable is the selected dimension
            ind_dim=np.where(np.array(var_dict["dim"])==dim_selected)[0][0]
            try:
                data_selected[varname]=np.take(data_selected[varname],ind_selected,axis=ind_dim)
            except:
                    breakpoint()
    return data_selected

def compute_iso_displacements(timeval,depthval,data_var,dvar,delta_smooth=10,zmin=0,dz=1,nmin=10,mindur=1):
    """
    Compute displacements of the isolines of a given field.
    
    Inputs:
        timeval (1d numpy array): timevalues in seconds from 01-01-1970
        depthval (1d numpy array): depth values [m]
        dvar (1d numpy array): step between isolines
        delta_smooth (int): number of data points to average for temporal smoothing
        zmin (float): minimum depth below which isolines are computed [m]
        dz (float): depth step to compute depth of isolines [m] --> not needed apparently
        nmin (int): minimum number of values needed to ompute trend
        mindur (float): minimum duration spanned by the data to calculate trend [yr]
    """
    # depth_trend=np.arange(depthval[0],depthval[-1],dz)
    var_trend=np.arange(round(np.nanmin(data_var)/dvar)*dvar,round(np.nanmax(data_var)/dvar)*dvar,dvar)
    
    z_iso=np.full((len(var_trend),len(timeval)),np.nan)
    data_smooth=movmean(data_var,delta_smooth,axis=1) # Temporal smoothing
    for kp in range(len(timeval)):
        # Get location of isolines: could be problematic when non monotic changes in the data (several locations for the same isoline)
        # Do not consider the upper 100 m for temperature because decreasing T with depth
        data_prof=data_smooth[:,kp]
        data_prof[depthval<zmin]=np.nan
        indsort=np.argsort(data_prof) # Sort values
        z_iso[:,kp]=np.interp(var_trend,data_prof[indsort],depthval[indsort],left=np.nan,right=np.nan) 
       
    # Calculate trends of isolines movements
    trend_iso_avg=(z_iso[:,-1]-z_iso[:,0])/(timeval[-1]-timeval[0])*3600*24*365 # m/yr
    
    trend_prof=np.full((len(var_trend),),np.nan) # Profile of trends
                
    for kz in range(len(var_trend)):
        if sum(~np.isnan(z_iso[kz,:]))>nmin: # At least nmin samples
            indval0=np.where(~np.isnan(z_iso[kz,:]))[0][0]# First profile used
            indvalf=np.where(~np.isnan(z_iso[kz,:]))[0][-1]# Last profile used
            if (timeval[indvalf]-timeval[indval0])>=mindur*365*24*3600: # At least duration of mindur years
                pfit,_,_,_=regression_oneline(timeval/(3600*24*365),z_iso[kz,:])
                trend_prof[kz]=pfit[0] # m/yr
    trend_iso_fit=trend_prof
    
    return trend_iso_avg,trend_iso_fit,z_iso,var_trend

# def compute_N2(zval,rhoval,windowsize=10,g=9.81):
#     # zval increases downward
#     zval=zval.reshape(-1,1) # column vector
#     rho_smooth=movmean(rhoval,windowsize,axis=0)
     
#     rho0=np.nanmean(rho_smooth,axis=0)
#     N2=np.full(rho_smooth.shape,np.nan)
#     N2[1:,:]=1/rho0*np.diff(rho_smooth,axis=0)/np.diff(zval,axis=0)*g
#     return N2 

def create_mixed_layer(zval,profval,zML_bot,zML_top):
    profmixed=profval.copy()
    avgval=np.nanmean(profval[np.logical_and(zval>zML_top,zval<zML_bot)])
    profmixed[np.logical_and(zval>zML_top,zval<zML_bot)]=avgval
    
    return avgval,profmixed

def export_to_netcdf(general_attributes,dimensions,variables,data,filename, mode='a', time_label="time",):
    log("Saving to NetCDF", indent=1)


    log("Writing data to NetCDF file {}".format(filename), indent=1)
 
    nc = netCDF4.Dataset(filename, mode='w', format='NETCDF4')
    
    try:

        for key in general_attributes:
            setattr(nc, key, general_attributes[key])
    
        for key, values in dimensions.items():
            nc.createDimension(values['dim_name'], values['dim_size'])
    
        for key, values in variables.items():
            var = nc.createVariable(values["var_name"], np.float64, values["dim"], fill_value=np.nan)
            var.units = values["unit"]
            var.long_name = values["longname"] 
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