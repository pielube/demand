

import numpy as np
import pandas as pd

from simulation import load_config
from functions import HPSizing, HouseHeating, load_climate_data
from demands import compute_demand
import defaults

import os
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

index1min  = pd.date_range(start='2015-01-01',end='2015-12-31 23:59:00',freq='T')
index10min = pd.date_range(start='2015-01-01',end='2015-12-31 23:59:00',freq='10T')
index15min = pd.date_range(start='2015-01-01',end='2015-12-31 23:59:00',freq='15T')
n15min = len(index15min)
ts15min = 1/4

heatseas_st = 305
heatseas_end = 105

temp, irr = load_climate_data()
temp = pd.Series(data=temp[:-1],index=index1min)
temp15min = temp.resample('15Min').mean()
irr = pd.Series(data=irr[:-1],index=index1min)
irr15min = irr.resample('15Min').mean()

conf = load_config('mattia')
config,pvbatt_param,econ_param,housetype,N = conf['config'],conf['pvbatt_param'],conf['econ_param'],conf['housetype'],conf['N']

procebinp = {
             'Aglazed': 21.0,
             'Aopaque': 271.1,
             'Afloor': 90.0,
             'volume': 630.0,
             'Atotal': 474.0,
             'Uwalls': 0.4,
             'Uwindows': 3.0,
             'ACH_vent': 0.5,
             'ACH_infl':0.0,
             'VentEff': 0.0,
             'Ctot': 16698806.0,
             'Uavg': 0.0}

members = ['FTE']

isolation = [0.2,0.4,0.6,0.8,1]
memberslist = [['FTE'],['Retired'],['FTE','FTE'],['Retired','Retired'],['FTE','PTE','U12'],['FTE','PTE','School'],['FTE','PTE','School','U12'],['FTE','PTE','School','School','U12']]

# isolation = [0.2]
# memberslist = [['FTE']]

for i in range(len(isolation)):
    procebinp['Uwalls'] = isolation[i]
    for j in range(len(memberslist)):
        members = memberslist[j]

        out = compute_demand(housetype,N,members= members,thermal_parameters=procebinp)
        occ = out['occupancy'][0]
        occupancy_10min = (occ==1).sum(axis=1) # when occupancy==1, the person is in the house and not sleeping
        occupancy_10min = (occupancy_10min>0)  # if there is at least one person awake in the house
        occupancy_15min = occupancy_10min.reindex(index15min,method='nearest')
        
        housetype['HP'] = {**housetype['HP'],**procebinp}
        
        Tset_ref = np.full(n15min,defaults.T_sp_low) + np.full(n15min,defaults.T_sp_occ-defaults.T_sp_low) * occupancy_15min
        
        housetype['HP']['HeatPumpThermalPower'] = None
        fracmaxP = 0.8
        QheatHP = HPSizing(housetype,fracmaxP)
        
        
        Qintgains = out['results'][0]['InternalGains']
        Qintgains = Qintgains.resample('15Min').mean() 
        res = HouseHeating(housetype,QheatHP,Tset_ref,Qintgains,temp15min,irr15min,n15min,heatseas_st,heatseas_end,ts15min)
        Qheat = res['Qheat']
        
        res = pd.DataFrame(data=Qheat,index=index15min,columns=['heat'])
        res['occupancy']=occupancy_15min
        
        namecsv = '\\isolation_'+str(i+1)+'_members_'+str(j+1)+'.csv'
        outpath = __location__ +'\\resmattia'+ namecsv
        res.to_csv(outpath)
  







