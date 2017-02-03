
from lib_compute_resilience_and_risk import *
from replace_with_warning import *
import os, time
import warnings
warnings.filterwarnings("always",category=UserWarning)
import numpy as np
import pandas as pd

optionFee="tax"
optionPDS="no"

if optionFee=="insurance_premium":
    optionB='unlimited'
    optionT='perfect'
else:
    optionB='data'
    optionT='data'
	
print('optionFee =',optionFee, 'optionPDS =', optionPDS, 'optionB =', optionB, 'optionT =', optionT)

#Options and parameters
#optionRUNPHL = ""
#economy= 'country' #province, deparmtent
optionRUNPHL = "PHL_"
economy= 'province'

event_level = [economy, "hazard", "rp"]	#levels of index at which one event happens
default_rp = "default_rp" #return period to use when no rp is provided (mind that this works with protection)
income_cats   = pd.Index(["poor","nonpoor"],name="income_cat")	#categories of households
affected_cats = pd.Index(["a", "na"]            ,name="affected_cat")	#categories for social protection
helped_cats   = pd.Index(["helped","not_helped"],name="helped_cat")

#read data
macro = pd.read_csv("intermediate/"+optionRUNPHL+"macro.csv", index_col=economy).dropna()
cat_info = pd.read_csv("intermediate/"+optionRUNPHL+"cat_info.csv",  index_col=[economy, "income_cat"]).dropna()
hazard_ratios = pd.read_csv("intermediate/"+optionRUNPHL+"hazard_ratios.csv", index_col=event_level+["income_cat"]).dropna()

#groups =  pd.read_csv("inputs/income_groups.csv",header =4,index_col=2)
#country_per_gp = groups["Income group"].reset_index().dropna().set_index("Income group").squeeze()
#country_per_rg = groups["Region"].reset_index().dropna().set_index("Region").squeeze()

#compute
macro_event, cats_event, hazard_ratios_event, macro = process_input(macro,cat_info,hazard_ratios,economy,event_level,default_rp,verbose_replace=True) 
#verbose_replace=True by default, replace common columns in macro_event and cats_event with those in hazard_ratios_event

macro_event, cats_event_ia = compute_dK(macro_event, cats_event,event_level,affected_cats) 
#calculate the actual vulnerability, the potential damange to capital, and consumption

macro_event, cats_event_iah = calculate_response(macro_event,cats_event_ia,event_level,helped_cats,
                                                 optionFee=optionFee, # optionFee="insurance_premium" (ALT: tax)
                                                 optionT=optionT, # optionT (targeting errors) = "perfect" (ALT: prop_nonpoor_lms, data, x33, incl, excl.)
                                                 optionPDS=optionPDS, # optionPDS: unif_poor, no, "prop", "prop_nonpoor"
                                                 optionB=optionB, # optionB:one_per_affected, one_per_helped, one, unlimited, data, unif_poor, max01, max05
                                                 loss_measure="dk",fraction_inside=1, share_insured=.25)

macro_event.to_csv('output/'+optionRUNPHL+'macro_'+optionFee+'_'+optionPDS+'.csv',encoding="utf-8", header=True)
cats_event_iah.to_csv('output/'+optionRUNPHL+'cats_event_iah_'+optionFee+'_'+optionPDS+'.csv',encoding="utf-8", header=True)   

out = compute_dW(macro_event,cats_event_iah,event_level,return_stats=True,return_iah=True)


results,iah = process_output(macro,out,macro_event,economy,default_rp,return_iah=True,is_local_welfare=True)
results.to_csv('output/'+optionRUNPHL+'results_'+optionFee+'_'+optionPDS+'.csv',encoding="utf-8", header=True)
iah.to_csv('output/'+optionRUNPHL+'iah_'+optionFee+'_'+optionPDS+'.csv',encoding="utf-8", header=True)


# result1=pd.read_csv("output-old/results.csv", index_col=economy)
# iah1=pd.read_csv("output-old/iah.csv", index_col=event_level+["income_cat","affected_cat","helped_cat"])
# print(((result1-results)/results).max())
# print(((iah1-iah.reset_index().set_index(event_level+["income_cat","affected_cat","helped_cat"]))/iah1).max())
