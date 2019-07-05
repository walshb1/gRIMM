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
df = df.set_index(list(df.columns[:7]))

arcope = ['Argentina','Colombia','Peru']
haz = ['fluvial flood','pluvial flood']

# Caculate Income Losses
df['di'] = df['dc_npv_pre']- df['dk']
eta = 1.5
# Calculate Well Being Losses in $equivalents.
df['dw_ceq'] = df['dw']/(df['c']**-eta)


slice_on = [0,1,2,3,5]
# weighted average the columns in wa, and mean the others.
wa = ['di','dc','dw','dc_npv_pre','dc_npv_post','help_needed','dw_ceq']
df[wa] = (df[wa].values.T * df['n'].values).T
d = df.groupby(level = slice_on).mean().copy()
d['n'] = df['n'].groupby(level = slice_on).sum()
d[wa] = df[wa].groupby(level = slice_on).sum()
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

# Split results by source
model        = os.getcwd() #get current directory
inputs       = model+'/inputs/' #get inputs data directory
intermediate = model+'/intermediate/' #get outputs data directory
pol_str = ''
hazard_ratios = pd.read_csv(intermediate+'hazard_ratios'+pol_str+".csv").dropna()
results_index = hazard_ratios.set_index(['country', 'source']).index # pd.MultiIndex.from_tuples(hazard_ratios.apply(lambda x: (x.country, x.source), axis =1))
hazard_ratios[economy] = hazard_ratios.apply(lambda x: (x.country+'_'+x.source), axis =1)
hazard_ratios = hazard_ratios.set_index(event_level+["income_cat"]).drop('source', axis =1)
tuple_filter = hazard_ratios.index.levels[0]

def reindex(df, tuple_filter=tuple_filter, results_index=results_index, broadcast = True):
    names = df.index.names
    if broadcast:
        df = broadcast_simple(df, results_index)
    df = df.reset_index()
    df[economy] = df.reset_index().apply(lambda x: (x.country+'_'+x.source), axis =1)
    df = df.set_index(economy)
    df = df.loc[tuple_filter]
    df = df.reset_index().set_index(names).sort_index()
    return df.dropna().drop('source', axis =1)


#define directory
use_published_inputs = False

model        = os.getcwd() #get current directory
inputs       = model+'/inputs/' #get inputs data directory
intermediate = model+'/intermediate/' #get outputs data directory

if use_published_inputs:
    inputs       = model+'/orig_inputs/' #get inputs data directory
    intermediate = model+'/orig_intermediate/' #get outputs data directory

# event_level.insert(1, 'source')
pol_str = ''
print(pol_str)
optionFee="tax"
optionPDS="unif_poor"

if optionFee=="insurance_premium":
    optionB='unlimited'
    optionT='perfect'
else:
    optionB='data'
    optionT='data'

print('optionFee =',optionFee, 'optionPDS =', optionPDS, 'optionB =', optionB, 'optionT =', optionT)

#Options and parameters
economy= "country" #province, deparmtent
event_level = [economy,"hazard", "rp"]	#levels of index at which one event happens
default_rp = "default_rp" #return period to use when no rp is provided (mind that this works with protection)
income_cats   = pd.Index(["poor","nonpoor"],name="income_cat")	#categories of households
affected_cats = pd.Index(["a", "na"]            ,name="affected_cat")	#categories for social protection
helped_cats   = pd.Index(["helped","not_helped"],name="helped_cat")

# Toggle to make country a country, source tuple
if True:
    # Check and make unique countries for each data source
    hazard_ratios = pd.read_csv(intermediate+'hazard_ratios'+pol_str+".csv").dropna()
    results_index = hazard_ratios.set_index(['country', 'source']).index # pd.MultiIndex.from_tuples(hazard_ratios.apply(lambda x: (x.country, x.source), axis =1))

    hazard_ratios[economy] = hazard_ratios.apply(lambda x: (x.country+'_'+x.source), axis =1)
    hazard_ratios = hazard_ratios.set_index(event_level+["income_cat"]).drop('source', axis =1)

    tuple_filter = hazard_ratios.index.levels[0]


    def reindex(df, tuple_filter=tuple_filter, results_index=results_index, broadcast = True):
        names = df.index.names
        if broadcast:
            df = broadcast_simple(df, results_index)
        df = df.reset_index()
        df[economy] = df.reset_index().apply(lambda x: (x.country+'_'+x.source), axis =1)
        df = df.set_index(economy)
        df = df.loc[tuple_filter]
        df = df.reset_index().set_index(names).sort_index()
        return df.dropna().drop('source', axis =1)

    macro = pd.read_csv(intermediate+'macro'+pol_str+".csv", index_col=economy).dropna()
    macro = reindex(macro)
    cat_info = reindex(pd.read_csv(intermediate+'cat_info'+pol_str+".csv",  index_col=[economy, "income_cat"]).dropna())
    groups =  pd.read_csv(inputs+"income_groups.csv",header =4,index_col=2)
    country_per_gp = groups["Income group"].reset_index().dropna().set_index("Income group").squeeze()
    country_per_rg = groups["Region"].reset_index().dropna().set_index("Region").squeeze()

else:
    #read data
    hazard_ratios = pd.read_csv(intermediate+'hazard_ratios'+pol_str+".csv", index_col=event_level+["income_cat"]).dropna()
    macro = pd.read_csv(intermediate+'macro'+pol_str+".csv", index_col=economy).dropna()
    # broadcast_simple(macro,hazard_ratios.reset_index().set_index(['country','source']).index.loc[hazard_ratios.index.codes]
    cat_info = pd.read_csv(intermediate+'cat_info'+pol_str+".csv",  index_col=[economy, "income_cat"]).dropna()
    groups =  pd.read_csv(inputs+"income_groups.csv",header =4,index_col=2)
    country_per_gp = groups["Income group"].reset_index().dropna().set_index("Income group").squeeze()
    country_per_rg = groups["Region"].reset_index().dropna().set_index("Region").squeeze()

#compute
macro_event, cats_event, hazard_ratios_event, macro = process_input(pol_str,macro,cat_info,hazard_ratios,economy,event_level,default_rp,verbose_replace=True) #verbose_replace=True by default, replace common columns in macro_event and cats_event with those in hazard_ratios_event
# cats_event = cats_event.fillna(0)
macro_event, cats_event_ia = compute_dK(macro_event, cats_event,event_level,affected_cats) #calculate the actual vulnerability, the potential damange to capital, and consumption

macro_event, cats_event_iah = calculate_response(macro_event,cats_event_ia,event_level,helped_cats,optionFee=optionFee,optionT=optionT, optionPDS=optionPDS, optionB=optionB,loss_measure="dk",fraction_inside=1, share_insured=.25)
#optionFee: tax or insurance_premium  optionFee="insurance_premium",optionT="perfect", optionPDS="prop", optionB="unlimited",optionFee="tax",optionT="data", optionPDS="unif_poor", optionB="data",
#optionT(targeting errors):perfect, prop_nonpoor_lms, data, x33, incl, excl.
#optionB:one_per_affected, one_per_helped, one, unlimited, data, unif_poor, max01, max05
#optionPDS: unif_poor, no, "prop", "prop_nonpoor"

def clean_index(df):
    df = df.reset_index()
    df['source'] = df[economy].apply(lambda x: (x[x.index('_')+1:]))
    df['country'] = df[economy].apply(lambda x: x[:x.index('_')])
    return df.set_index(['country','source'])


# Compute dW normally for this policy and dataset
out = compute_dW(macro_event,cats_event_iah,event_level,return_stats=True,return_iah=True, arcope = False)
dkdw_event,cats_event_iah  = out
dkdw_h = average_over_rp(dkdw_event,default_rp,macro_event["protection"])

# # Get flood data only and drop the rest
# dkdw_flood = dkdw_h.loc[idx[:,'flood'],].reset_index().set_index(economy).drop('hazard',axis = 1)
# For what indicators is summing across different hazards a problem and for what is it good?
dkdw = dkdw_h.sum(level=economy) # # There's a bug in how these are aggregated in the main script

# addition - make sure we're not adding the thing into dkdw
av_lis = ['c','gamma_SP','n','k','social','v','v_shew', 'shew', 'axfin']
for i in av_lis:
    dkdw[i] = dkdw_h[i].mean(level=economy)


# Now look at top80% vs bottom 20%

cats_event_iah = cats_event_iah.reset_index().set_index(hh_level)
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

dkdw_income_cat = dkdw_income_cat.dropna()

def get_dkdw(df_income_cat, ic= 'total'):
    try:
        dkdw_ic = df_income_cat.loc[idx[:,:,ic],].droplevel(level = -1)
    except:
        dkdw_ic = df_income_cat.loc[idx[:,ic],].droplevel(level = -1)
    dkdw2 = dkdw_ic.sum(level=economy) # There's a bug in how these are aggregated in the main script
    for i in av_lis:
        dkdw2[i] = dkdw_ic[i].mean(level=economy)
    print(ic)
    dkdw2['income_cat'] = ic
    return dkdw2

dfs = []
for i in ['total','nonpoor','poor']:
    _dkdw = get_dkdw(dkdw_income_cat,i)
    macro[_dkdw.columns]=_dkdw
    _macro = calc_risk_and_resilience_from_k_w(macro, is_local_welfare, arcope = True)
    dfs.append(_macro)

df = pd.concat(dfs)
df = df.reset_index().set_index(['country','income_cat']).sort_index()
df['income_losses_pre'] = df['dc_npv_pre']-df['dK']
df['income_losses_post'] = df['dc_npv_post']-df['dK']

df2 = df[['income_losses_pre','income_losses_post','dc_npv_pre','dc_npv_post','dWpc_currency','risk','risk_to_assets','resilience']]


df2.columns = ['Income Losses before social transfers','Income Losses after social transfers','Consumption Losses without social transfers','Consumption Losses with social Transfers','Welfare Losses','Risk to Well-being','Risk to Assets','Resilience']
df2 = clean_index(df2).reset_index().set_index(['country','source','income_cat'])
df2 = df2.drop_duplicates()
df2.loc[['Argentina','Colombia','Peru']].unstack().round(4).T.to_csv('acp_all_haz.csv')
df.to_csv('results_arcope.csv')
