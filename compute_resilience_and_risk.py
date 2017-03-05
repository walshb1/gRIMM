
from lib_compute_resilience_and_risk import *
from replace_with_warning import *
import os, time
import warnings
warnings.filterwarnings("always",category=UserWarning)
import numpy as np
import pandas as pd

optionFee="tax"
optionPDS="no"

option_social = '' # { <any float> }
option_shew   = '' # { 'shew100' }
option_rshar  = True # { True or False }

if optionFee=="insurance_premium":
    optionB='unlimited'
    optionT='perfect'
else:
    optionB='data'
    optionT='data'
	
print('optionFee =',optionFee, 'optionPDS =', optionPDS, 'optionB =', optionB, 'optionT =', optionT)

#Options and parameters
optionRUNPHL = "PHL_"
economy= 'province'

event_level = [economy, "hazard", "rp"]	#levels of index at which one event happens
default_rp = "default_rp" #return period to use when no rp is provided (mind that this works with protection)
income_cats   = pd.Index(["poor","nonpoor"],name="income_cat")	#categories of households
affected_cats = pd.Index(["a", "na"]            ,name="affected_cat")	#categories for social protection
helped_cats   = pd.Index(["helped","not_helped"],name="helped_cat")

#read data
macro = pd.read_csv("intermediate/PHL_macro.csv", index_col=economy).dropna()
cat_info = pd.read_csv("intermediate/PHL_cat_info.csv",  index_col=[economy, "income_cat"]).fillna(0)
hazard_ratios = pd.read_csv("intermediate/PHL_hazard_ratios.csv", index_col=event_level+["income_cat"]).dropna()

if option_social != '' and float(option_social):
    macro['social_p']*=(1.0+float(option_social))
    macro['social_r']*=(1.0+float(option_social))
    cat_info['social']*=(1.0+float(option_social))
else: 
    pass

if option_shew == 'shew100':
    
    macro.shewp = 1.0
    macro.shewr = 1.0
    
    cat_info.shew = 1.0

    #shew still 0 for earthquakes
    hazard_ratios.shew = 1.0
    hazard_ratios['shew']=hazard_ratios.shew.unstack("hazard").assign(earthquake=0).stack("hazard").reset_index().set_index(event_level+[ "income_cat"]) 
else: 
    pass

if option_rshar:
    # True: this reduces dk by 30% in compute_dk function
    str_rshar = 'rshar'
else:
    str_rshar = ''
    # False: pass
    
#compute
macro_event, cats_event, hazard_ratios_event, macro = process_input(macro,cat_info,hazard_ratios,economy,event_level,default_rp,verbose_replace=True) 
#verbose_replace=True by default, replace common columns in macro_event and cats_event with those in hazard_ratios_event

macro_event, cats_event_ia = compute_dK(macro_event, cats_event,event_level,affected_cats,option_rshar) 
#calculate the actual vulnerability, the potential damange to capital, and consumption

macro_event, cats_event_iah = calculate_response(macro_event,cats_event_ia,event_level,helped_cats,
                                                 optionFee=optionFee, # optionFee="insurance_premium" (ALT: tax)
                                                 optionT=optionT, # optionT (targeting errors) = "perfect" (ALT: prop_nonpoor_lms, data, x33, incl, excl.)
                                                 optionPDS=optionPDS, # optionPDS: unif_poor, no, "prop", "prop_nonpoor"
                                                 optionB=optionB, # optionB:one_per_affected, one_per_helped, one, unlimited, data, unif_poor, max01, max05
                                                 loss_measure="dk",fraction_inside=1, share_insured=.25)


options_string = (optionFee+'_'+optionPDS+'_'+option_shew+'_'+option_social+'_'+str_rshar+'.csv').replace('__','_').replace('_.','.')

macro_str = ('output/PHL_macro_'+options_string).replace('__','_')
cats_event_str = ('output/PHL_cats_event_iah_'+options_string).replace('__','_')

macro_event.to_csv(macro_str,encoding="utf-8", header=True)
cats_event_iah.to_csv(cats_event_str,encoding="utf-8", header=True)   

out = compute_dW(macro_event,cats_event_iah,event_level,return_stats=True,return_iah=True)

results_str = ('output/PHL_results_'+options_string).replace('__','_')
iah_str = ('output/PHL_iah_'+options_string).replace('__','_')

results,iah = process_output(macro,out,macro_event,economy,default_rp,return_iah=True,is_local_welfare=True)
results.to_csv(results_str,encoding="utf-8", header=True)
iah.to_csv(iah_str,encoding="utf-8", header=True)

# result1=pd.read_csv("output-old/results.csv", index_col=economy)
# iah1=pd.read_csv("output-old/iah.csv", index_col=event_level+["income_cat","affected_cat","helped_cat"])
# print(((result1-results)/results).max())
# print(((iah1-iah.reset_index().set_index(event_level+["income_cat","affected_cat","helped_cat"]))/iah1).max())
