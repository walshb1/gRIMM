from res_ind_lib import *
from lib_compute_resilience_and_risk import *

from replace_with_warning import *
import os, time
import warnings
warnings.filterwarnings("always",category=UserWarning)
import numpy as np
import pandas as pd
idx = pd.IndexSlice


# Exploration work, how do we splot by household?
df = pd.read_csv('output/iah_tax_unif_poor_.csv')
df = df.set_index(list(df.columns[:6]))

arcope = ['Argentina','Colombia','Peru']
haz = ['flood']

# Caculate Income Losses
df['di'] = df['dc_npv_pre']- df['dk']
eta = 1.5
# Calculate Well Being Losses in $equivalents.
df['dw_ceq'] = df['dw']/(df['c']**-eta)

# weighted average the columns in wa, and mean the others.
wa = ['di','dc','dw','dc_npv_pre','dc_npv_post','help_needed','dw_ceq']
df[wa] = (df[wa].values.T * df['n'].values).T
d = df.groupby(level = [0,1,2,4]).mean().copy()
d['n'] = df['n'].groupby(level = [0,1,2,4]).sum()
d[wa] = df[wa].groupby(level = [0,1,2,4]).sum()
d[wa] = (d[wa].values.T/d['n'].values).T
df = d

dk = average_over_rp(df,'default_rp')

dk['Asset Losses'] = dk['dk']/dk['k']

for i in ['Income Losses','Consumption Losses','Well Being Losses']:
    dk[i] = None
dk[['Income Losses','Consumption Losses','Well Being Losses']] = 100*(dk[['di','dc_npv_pre','dw_ceq']].values.T/dk['c'].values).T




# Options and Parameters
default_rp = 'default_rp'
economy="country" #province, deparmtent
event_level = [economy, "hazard", "rp"]	#levels of index at which one event happens
hh_level = event_level+['income_cat'] # splitting by income category
is_local_welfare = True

# Split results by hazard
macro = pd.read_csv('intermediate/'+'macro'+'_un'+".csv", index_col=economy).dropna()
macro_event = pd.read_csv('output/macro_tax_unif_poor_.csv').set_index(event_level)
cats_event_iah = pd.read_csv('output/cats_event_iah_tax_unif_poor_.csv').set_index(event_level)


# Compute dW normally for this policy and dataset
out = compute_dW(macro_event,cats_event_iah,event_level,return_stats=True,return_iah=True, arcope = False)
dkdw_event,cats_event_iah  = out
dkdw_h = average_over_rp(dkdw_event,default_rp,macro_event["protection"])

# Get flood data only and drop the rest
dkdw_flood = dkdw_h.loc[idx[:,'flood'],].reset_index().set_index(economy).drop('hazard',axis = 1)
# For what indicators is summing across different hazards a problem and for what is it good?
dkdw = dkdw_h.sum(level=economy) # # There's a bug in how these are aggregated in the main script

# addition - make sure we're not adding the thing into dkdw
av_lis = ['c','gamma_SP','n','k','social','v','v_shew', 'shew', 'axfin']
for i in av_lis:
    dkdw[i] = dkdw_h[i].mean(level=economy)


# Now look at top80% vs bottom 20%
cats_event_iah = pd.read_csv('output/cats_event_iah_tax_unif_poor_.csv').set_index(hh_level)
out = compute_dW(macro_event,cats_event_iah,hh_level,return_stats=True,return_iah=True,arcope = True)
dkdw_event,cats_event_iah  = out
# drop duplicates drops rps with same stats (e.g. non-effects)
dkdw_event = dkdw_event.loc[~dkdw_event.index.duplicated(keep='first')]
# now rearrange into two diff arrays for poor and nonpoor
dkdw_poor = dkdw_event.loc[idx[:,:,:,'poor'],].reset_index(-1).drop('income_cat',axis = 1)
dkdw_nonpoor = dkdw_event.loc[idx[:,:,:,'nonpoor'],].reset_index(-1).drop('income_cat',axis = 1)


dkdw_h_poor = average_over_rp(dkdw_poor,default_rp,arcope = True)
dkdw_h_poor['income_cat'] = 'poor'
dkdw_h_nonpoor = average_over_rp(dkdw_nonpoor,default_rp,arcope = True)
dkdw_h_nonpoor['income_cat'] = 'nonpoor'
dkdw_h['income_cat'] = 'total'



dkdw_income_cat = pd.concat((dkdw_h_poor,dkdw_h_nonpoor,dkdw_h)).reset_index().set_index([economy,'hazard','income_cat']).sort_index()

dkdw_income_cat = (dkdw_income_cat.T/dkdw_income_cat['n']).T
dkdw_income_cat_flood = dkdw_income_cat.loc[idx[:,'flood'],].reset_index().set_index([economy,'income_cat']).drop('hazard',axis = 1)



def get_dkdw(df_income_cat, ic= 'total'):
    dkdw_ic = df_income_cat.loc[idx[:,:,ic],].droplevel(level = -1)
    dkdw2 = dkdw_ic.sum(level=economy) # There's a bug in how these are aggregated in the main script
    for i in av_lis:
        dkdw2[i] = dkdw_ic[i].mean(level=economy)

    dkdw2['income_cat'] = ic
    return dkdw2

dfs = []
for i in ['total','nonpoor','poor']:
    _dkdw = get_dkdw(dkdw_income_cat,i)
    macro[_dkdw.columns]=get_dkdw(dkdw_income_cat,i)
    _macro = calc_risk_and_resilience_from_k_w(macro, is_local_welfare, arcope = True)
    dfs.append(_macro)




df = pd.concat(dfs).reset_index().set_index(['country','income_cat']).sort_index()
df['income_losses_pre'] = df['dc_npv_pre']-df['dK']
df['income_losses_post'] = df['dc_npv_post']-df['dK']


df2 = df[['income_losses_pre','income_losses_post','dc_npv_pre','dc_npv_post','dWpc_currency','risk','risk_to_assets','resilience']]
df2.loc[['Argentina','Colombia','Peru']].T
df.to_csv('results_arcope.csv')
