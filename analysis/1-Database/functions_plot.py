import os
import sys
import json
import math
import numpy as np
import pandas as pd
import gsw
import seawater as sw
from shutil import copyfile
from envass import qualityassurance
from datetime import datetime, timedelta, timezone
import time
from scipy.ndimage import uniform_filter1d
from sklearn.linear_model import LinearRegression
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
#sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Functions'))
from functions import *


def plot_trend_series(methods_all,data_comb,indprof,delta=False,intersect_lines=True,datetime_extract=datetime(2016,1,1),xlimval=(datetime(2008,1,1),datetime(2023,1,1)),ylimval=(254,266),savefig_bool=False):
    # If delta is true, plot delta_meta
    fig,ax_all=plt.subplots(len(methods_all),1,figsize=(8,8),sharey=True,sharex=True)
    if len(methods_all)==1:
        ax_all=[ax_all]
    
    for kmethod in range(len(methods_all)):
        # exec('zchem_gov=data_gov.'+methods_all[kmethod])
        # exec('zchem_KW=data_KW.'+methods_all[kmethod])
        zchem_comb=eval('data_comb.'+methods_all[kmethod])

        indgov=indprof[np.where(data_comb.data_type.values[indprof]==0)]
        indKW=indprof[np.where(data_comb.data_type.values[indprof]==1)]
        date_extract=np.datetime64(datetime_extract)
        # pfit_gov,t_gov,zfit_gov,R2_gov=regression_period(data_gov.time.values.astype(np.int64)*1e-9,zchem_gov,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
        # pfit_KW,t_KW,zfit_KW,R2_KW=regression_period(data_KW.time.values.astype(np.int64)*1e-9,zchem_KW,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp())
        pfit_comb,t_comb,zfit_comb,R2_comb=regression_period(data_comb.time.values[indprof].astype(np.int64)*1e-9,zchem_comb[indprof],datetime_extract.replace(tzinfo=timezone.utc).timestamp())
        # pfit_gov2,zfit_gov2,R2_gov2,pcov_gov2=regression_period_intersect(data_gov.time.values.astype(np.int64)*1e-9,zchem_gov,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
        # pfit_KW2,zfit_KW2,R2_KW2,pcov_KW2=regression_period_intersect(data_KW.time.values.astype(np.int64)*1e-9,zchem_KW,datetime(2016,1,1).replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
        pfit_comb2,zfit_comb2,R2_comb2,pcov_comb2=regression_period_intersect(data_comb.time.values[indprof].astype(np.int64)*1e-9,zchem_comb[indprof],datetime_extract.replace(tzinfo=timezone.utc).timestamp(),[1,1,1])
        
        
        ax=ax_all[kmethod]
        ax.set_title('Method: '+methods_all[kmethod],fontsize=12)

        
        xtext=date_extract+0.25*(np.datetime64(xlimval[1])-np.datetime64(xlimval[0]))
        #ytext=ylimval[0]+0.05*(ylimval[1]-ylimval[0])
        ytext=ylimval[0]+0.95*(ylimval[1]-ylimval[0])
   
        ax.plot(data_comb.time[indprof],zchem_comb[indprof],'k-')
        ax.plot(data_comb.time[indgov],zchem_comb[indgov],'.',color='C0')
        ax.plot(data_comb.time[indKW],zchem_comb[indKW],'.',color='C1')
        ax.plot([date_extract,date_extract],ylimval,'-b')
        if delta:
            increm='d$\\delta$'
        else:
            increm='dz'
        if intersect_lines:
            ax.plot(data_comb.time[indprof],zfit_comb2,'--r')
            ax.text(xtext,ytext,"{}/dt = {:.2f}$\\pm${:.2f} m/yr\n $R^2$ = {:.2f}".format(increm,pfit_comb2[1][0]*3600*24*365,np.sqrt(pcov_comb2[2,2])*3600*24*365,R2_comb2[1]),
                       color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})   
        else: 
            ax.plot([datetime.utcfromtimestamp(int(t_comb[0][i])) for i in np.arange(len(t_comb[0]))],zfit_comb[0],'--r')
            ax.plot([datetime.utcfromtimestamp(int(t_comb[1][i])) for i in np.arange(len(t_comb[1]))],zfit_comb[1],'--r')
            ax.text(xtext,ytext,"{}/dt = {:.2f} m/yr\n $R^2$ = {:.2f}".format(increm,pfit_comb[1][0]*3600*24*365,R2_comb[1]),
                       color='r',horizontalalignment='center',verticalalignment='bottom',bbox={"facecolor":"grey","alpha":0.2})
        if kmethod==0:
            ax.set_ylim(ylimval)        
            ax.set_xlim(xlimval)
            ax.invert_yaxis()
        if delta:
            ax.set_ylabel('$\\delta_{\\rm meta}$ [m]')
        else: 
            ax.set_ylabel('$z_{\\rm chem}$ [m]')
            
        
        
    if savefig_bool:
        if delta:
            fig.savefig("Figures/trend_delta_methods.png",dpi=400)  
            #fig.savefig("Figures/trend_delta_"+methods_all[kmethod]+".svg") 
        else:
            fig.savefig("Figures/trend_zchem_methods.png",dpi=400)  
            #fig.savefig("Figures/trend_zchem_"+methods_all[kmethod]+".svg")
            
        print('Figure saved')