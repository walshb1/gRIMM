#This script provides data input for the resilience indicator multihazard model. The script was developed by Adrien Vogt-Schilb and improved by Jinqiang Chen.

#Import package for data analysis
from lib_gather_data import *
from phllib_gather_data import *

from replace_with_warning import *
import numpy as np
import pandas as pd
from pandas import isnull
import os, time
import warnings
warnings.filterwarnings("always",category=UserWarning)  

#Options and parameters
do_reporting                 = False # True = verbose
protection_from_flopros      = True  #FLOPROS is an evolving global database of flood protection standards. It will be used in Protection.
no_protection                = True  #Used in Protection. 
use_guessed_social           = True  #else keeps nans
use_avg_pe                   = True  #otherwise 0 when no data
use_newest_wdi_findex_aspire = False  #too late to include new data just before report release
drop_unused_data             = False #if true removes from df and cat_info the intermediate variables
economy                      = "country" #province, department
# looks like this is the for switching from country to local level--instead, create a version of the code that works only for PHL

event_level = [economy, "hazard", "rp"]	#levels of index at which one event happens
default_rp = "default_rp" #return period to use when no rp is provided (mind that this works with protection)
income_cats   = pd.Index(["poor","nonpoor"],name="income_cat")	#categories of households
affected_cats = pd.Index(["a", "na"]            ,name="affected_cat")	#categories for social protection
helped_cats   = pd.Index(["helped","not_helped"],name="helped_cat")

#hazard_idx    = ['earthquake','flood','surge','tsunami','wind','typhoon']
#rp_idx        = pd.Index([10,25,30,50,100,200,250,500,1000],name='rp')
hazard_idx    = pd.Index(['earthquake','flood','surge','tsunami','wind','typhoon'], name='hazards')

asset_loss_covered  = 0.80
discount_rate       = 0.06
fa_threshold        = 0.90
inc_elast           = 1.50
max_support         = 0.05
poverty_head        = 0.20
reconstruction_time = 3.00
reduction_vul       = 0.20

# - Define directories
model        = os.getcwd() #get current directory
inputs       = model+'/inputs/' #get inputs data directory
PHLinputs    = model+'/inputs/PHL' #get inputs data directory
intermediate = model+'/intermediate/' #get outputs data directory
if not os.path.exists(intermediate): #if the depository directory doesn't exist, create one
    os.makedirs(intermediate)

# - Country dictionaries
any_to_wb  = pd.read_csv(inputs+"/any_name_to_wb_name.csv",index_col="any",squeeze=True)	#Names to WB names
iso3_to_wb = pd.read_csv(inputs+"/iso3_to_wb_name.csv").set_index("iso3").squeeze()	#iso3 to wb country name table
iso2_iso3  = pd.read_csv(inputs+"/names_to_iso.csv", usecols=["iso2","iso3"]).drop_duplicates().set_index("iso2").squeeze() #iso2 to iso3 table 

######################################
# ---> Global section
#

#Read data
##Macro data
###Economic data from the world bank
the_file = inputs+"wb_data_backup.csv"
nb_weeks = (time.time()-os.stat(the_file).st_mtime )/(3600*24*7) #calculate the nb of weeks since the last modified time
if nb_weeks > 20 and do_reporting: 
    warnings.warn("World bank data are "+str(int(nb_weeks))+" weeks old. You may want to download them again.")
df = pd.read_csv(the_file).set_index(economy)

df["urbanization_rate"]=pd.read_csv(inputs+"/wb_data.csv").set_index(economy)["urbanization_rate"]
df=df.drop(["plgp","unemp","bashs","ophe", "axhealth"],axis=1)	
# Drops here the data not used, to avoid it counting as missing data. 
# - What are included are:gdp_pc_pp, pop, share1, axfin_p, axfin_r, social_p, social_r, urbanization_rate.

###Define parameters
df["pov_head"]=poverty_head #poverty head
ph=df.pov_head

df["T_rebuild_K"] = reconstruction_time #Reconstruction time
df["pi"] = reduction_vul	# how much early warning reduces vulnerability
df["income_elast"] = inc_elast	#income elasticity
df["rho"] = discount_rate	#discount rate
df["shareable"]=asset_loss_covered  #target of asset losses to be covered by scale up
df["max_increased_spending"] = max_support # 5% of GDP in post-disaster support maximum, if everything is ready 

###Social transfer Data from EUsilc (European Union Survey of Income and Living Conditions) and other countries.
silc=pd.read_csv(inputs+"/social_ratios.csv") #XXX: there is data from ASPIRE in social_ratios. Use fillna instead to update df.
silc=silc.set_index(silc.cc.replace({"EL":"GR","UK":"GB"}).replace(iso2_iso3).replace(iso3_to_wb)) #Change indexes with wold bank names. UK and greece have differnt codes in Europe than ISO2. The first replace is to change EL to GR, and change UK to GB. The second one is to change iso2 to iso3, and the third one is to change iso3 to the wb
df.ix[silc.index,["social_p","social_r"]]  = silc[["social_p","social_r"]] #Update social transfer from EUsilc.
where=(isnull(df.social_r)&~isnull(df.social_p))|(isnull(df.social_p)&~isnull(df.social_r)) #shows the country where social_p and social_r are not both NaN.
if(do_reporting): 
    print("social_p and social_r are not both NaN for " + "; ".join(df.loc[where].index))
df.loc[isnull(df.social_r),['social_p','social_r']]=np.nan
df.loc[isnull(df.social_p),['social_p','social_r']]=np.nan

###Guess social transfer
guessed_social=pd.read_csv(inputs+"/df_social_transfers_statistics.csv", index_col=0)[["social_p_est","social_r_est"]]
guessed_social.columns=["social_p", "social_r"]
if use_guessed_social:
    df=df.fillna(guessed_social.clip(lower=0, upper=1)) #replace the NaN with guessed social transfer.

####HFA (Hyogo Framework for Action) data to assess the role of early warning system	
#2015 hfa
hfa15=pd.read_csv(inputs+"/HFA_all_2013_2015.csv")
hfa15=hfa15.set_index(replace_with_warning(hfa15["Country name"],any_to_wb))

# READ THE LAST HFA DATA
hfa_newest=pd.read_csv(inputs+"/HFA_all_2011_2013.csv")
hfa_newest=hfa_newest.set_index(replace_with_warning(hfa_newest["Country name"],any_to_wb))
# READ THE PREVIOUS HFA DATA
hfa_previous=pd.read_csv(inputs+"/HFA_all_2009_2011.csv")
hfa_previous=hfa_previous.set_index(replace_with_warning(hfa_previous["Country name"],any_to_wb))
#most recent values... if no 2011-2013 reporting, we use 2009-2011
hfa_oldnew=pd.concat([hfa_newest, hfa_previous, hfa15], axis=1,keys=['new', 'old', "15"]) #this is important to join the list of all countries
hfa = hfa_oldnew["15"].fillna(hfa_oldnew["new"].fillna(hfa_oldnew["old"]))
hfa["shew"]=1/5*hfa["P2-C3"] #access to early warning normalized between zero and 1. 
hfa["prepare_scaleup"]=(hfa["P4-C2"]+hfa["P5-C2"]+hfa["P4-C5"])/3/5 # q_s in the report, ability to scale up support to to affected population after the disaster, normalized between zero and 1
hfa["finance_pre"]=(1+hfa["P5-C3"])/6 #betwenn 0 and 1	!!!!!!!!!!!!!!!!!!!REMARK: INCONSISTENT WITH THE TECHNICAL PAPER. Q_f=1/2(ratings+P5C3/5)
df[["shew","prepare_scaleup","finance_pre"]]=hfa[["shew","prepare_scaleup","finance_pre"]]
df[["shew","prepare_scaleup","finance_pre"]]=df[["shew","prepare_scaleup","finance_pre"]].fillna(0)	#assumes no reporting is bad situation (caution! do the fillna after inputing to df to get the largest set of index)

###Country Ratings
the_credit_rating_file=inputs+"/cred_rat.csv"
nb_weeks=(time.time()-os.stat(the_credit_rating_file).st_mtime )/(3600*24*7)
if nb_weeks>3 and do_reporting:
    warnings.warn("Credit ratings are "+str(int(nb_weeks))+" weeks old. Get new ones at http://www.tradingeconomics.com/country-list/rating")
ratings_raw=pd.read_csv(the_credit_rating_file,dtype="str").dropna(how="all") #drop rows where only all columns are NaN.
ratings_raw=ratings_raw.rename(columns={"Unnamed: 0": "country_in_ratings"})[["country_in_ratings","S&P","Moody's","Fitch"]] #Rename "Unnamed: 0" to "country_in_ratings" and pick only columns with country_in_ratings, S&P, Moody's and Fitch.
ratings_raw.country_in_ratings= ratings_raw.country_in_ratings.str.strip().replace(["Congo"],["Congo, Dem. Rep."]) 
# NB: The credit rating sources calls DR Congo just Congo. Here str.strip() is needed to remove any space in the raw data. 
# -- In the raw data, Congo has some spaces after "o". If not used str.strip(), nothing is replaced.
ratings_raw["country"]= replace_with_warning(ratings_raw.country_in_ratings.apply(str.strip),any_to_wb)	#change country name to wb's name
ratings_raw=ratings_raw.set_index("country")
ratings_raw=ratings_raw.applymap(mystriper) #mystriper is a function in lib_gather_data. To lower case and strips blanks.    

#Transforms ratings letters into 1-100 numbers
rat_disc = pd.read_csv(inputs+"/cred_rat_dict.csv")
ratings=ratings_raw
ratings["S&P"].replace(rat_disc["s&p"].values,rat_disc["s&p_score"].values,inplace=True)
ratings["Moody's"].replace(rat_disc["moodys"].values,rat_disc["moodys_score"].values,inplace=True)
ratings["Fitch"].replace(rat_disc["fitch"].values,rat_disc["fitch_score"].values,inplace=True)
ratings["rating"]=ratings.mean(axis=1)/100 #axis=1 is the average across columns, axis=0 is to average across rows. .mean ignores NaN
df["rating"] = ratings["rating"]
if(do_reporting):
    print("some bad rating occurs for" + "; ".join(df.loc[isnull(df.rating)].index))
df["rating"].fillna(0,inplace=True)  #assumes no rating is bad rating

###Ratings + HFA
df["borrow_abi"]=(df["rating"]+df["finance_pre"])/2 # Ability and willingness to improve transfers after the disaster

##Capital data
k_data=pd.read_csv(inputs+"/capital_data.csv",usecols=["code","cgdpo","ck"]).replace({"ROM":"ROU","ZAR":"COD"}).rename(columns={"cgdpo":"prod_from_k","ck":"k"})#Zaire=Congo
iso_country = pd.read_csv(inputs+"/iso3_to_wb_name.csv", index_col="iso3")	#matches names in the dataset with world bank country names
k_data.set_index("code",inplace=True)
k_data["country"]=iso_country["country"]
cond = k_data["country"].isnull()
if cond.sum()>0 and do_reporting:
     warnings.warn("this countries appear to be missing from iso3_to_wb_name.csv: "+" , ".join(k_data.index[cond].values))
k_data=k_data.reset_index().set_index("country")
df["avg_prod_k"]=k_data["prod_from_k"]/k_data["k"] #\mu in the technical paper -- average productivity of capital

##Hazards data
###Vulnerability from Pager data
pager_description_to_aggregate_category = pd.read_csv(inputs+"/pager_description_to_aggregate_category.csv", index_col="pager_description", squeeze=True)
PAGER_XL = pd.ExcelFile(inputs+"/PAGER_Inventory_database_v2.0.xls")
pager_desc_to_code = pd.read_excel(PAGER_XL,sheetname="Release_Notes", parse_cols="B:C", skiprows=56).dropna().squeeze()
pager_desc_to_code.Description = pager_desc_to_code.Description.str.strip(". ")	#removes spaces and dots from PAGER description
pager_desc_to_code.Description = pager_desc_to_code.Description.str.replace("  "," ")	#replace double spaces with single spaces
pager_desc_to_code = pager_desc_to_code.set_index("PAGER-STR")
pager_code_to_aggcat = replace_with_warning( pager_desc_to_code.Description, pager_description_to_aggregate_category, joiner="\n") 
#results in a table with PAGER-STR index and associated category (fragile, median etc.)

###total share of each category of building per country
rural_share= .5*get_share_from_sheet(PAGER_XL,pager_code_to_aggcat,iso3_to_wb,sheetname='Rural_Non_Res')+.5*get_share_from_sheet(PAGER_XL,pager_code_to_aggcat,iso3_to_wb,sheetname='Rural_Res')
urban_sare = .5*get_share_from_sheet(PAGER_XL,pager_code_to_aggcat,iso3_to_wb,sheetname='Urban_Non_Res')+.5*get_share_from_sheet(PAGER_XL,pager_code_to_aggcat,iso3_to_wb,sheetname='Urban_Res')
share = (rural_share.stack()*(1-df.urbanization_rate) + urban_sare.stack()*df.urbanization_rate).unstack().dropna()	#the sum(axis=1) of rural_share is equal to 1, so rural_share needs to be weighted by the 1-urbanization_rate, same for urban_share
share=  share[share.index.isin(iso3_to_wb)] #the share of building inventory for fragile, median and robust

###matching vulnerability of buildings and people's income and calculate poor's, rich's and country's vulnerability
agg_cat_to_v = pd.read_csv(inputs+"/aggregate_category_to_vulnerability.csv", sep=";", index_col="aggregate_category", squeeze=True)
##REMARK: NEED TO BE CHANGED....Stephane I've talked to @adrien_vogt_schilb and don't want you to go over our whole conversation. Here is the thing: in your model, you assume that the bottom 20% of population gets the 20% of buildings of less quality. I don't think it's a fair jusfitication, because normally poor people live in buildings of less quality but in a more crowded way,i.e., it could be the bottom 40% of population get the 10% of buildings of less quality. I think we need to correct this matter. @adrien_vogt_schilb also agreed on that, if he didn't change his opinion. How to do that? I think once we incorporate household data, we can allocate buildings on the decile of households, rather than population. I think it's a more realistic assumption. 

# This assumes uniform density (see above) of people in buildings, and assigns the poor to the lowest quality buildings, starting from fragile then to median if necessary
p=(share.cumsum(axis=1).add(-df["pov_head"],axis=0)).clip(lower=0)
poor=(share-p).clip(lower=0)
rich=share-poor

vp_unshaved=((poor*agg_cat_to_v).sum(axis=1, skipna=False)/df["pov_head"] )
vr_unshaved=(rich*agg_cat_to_v).sum(axis=1, skipna=False)/(1-df["pov_head"])
v_unshaved =  vp_unshaved*df.share1 + vr_unshaved*(1-df.share1)
v_unshaved.name="v"
v_unshaved.index.name = "country"
vp = vp_unshaved.copy()
vr = vr_unshaved.copy()
v = v_unshaved.copy()

###apply \delta_K = f_a * V, and use destroyed capital from GAR data, and fa_threshold to recalculate vulnerability
# =Generated by pre_process\ GAR.ipynb

frac_value_destroyed_gar = pd.read_csv(inputs+"/frac_value_destroyed_gar_completed.csv", index_col=["country", "hazard", "rp"], squeeze=True);#\delta_K, 
fa_guessed_gar = (frac_value_destroyed_gar/broadcast_simple(v_unshaved,frac_value_destroyed_gar.index)).dropna()

#fa is the fraction of asset affected. broadcast_simple, substitute the value in frac_value_destroyed_gar by values in v_unshaved. 
# - Here it assumes that vulnerability for all types of disasters are the same. fa_guessed_gar = exposure/vulnerability
fa_guessed_gar.name  = "fa"

excess=fa_guessed_gar[fa_guessed_gar>fa_threshold].max(level="country")

for c in excess.index:
    r = (excess/fa_threshold)[c]
    print(c,r, fa_guessed_gar[fa_guessed_gar>fa_threshold].ix[c])
    fa_guessed_gar.update(fa_guessed_gar.ix[[c]]/r)  # i don't care.
    vp.ix[c] *= r
    vr.ix[c] *= r
    v.ix[c] *=r

vp = vp.clip(upper=.99)
vr = vr.clip(upper=.99)

###Exposure bias from PEB
data = pd.read_excel(inputs+"/PEB_flood_povmaps.xlsx")[["iso","peb"]].dropna()	#Exposure bias from WB povmaps study
df["pe"] = data.set_index(data.iso.replace(iso3_to_wb)).peb-1

PEB_wb_deltares_older = pd.read_csv(inputs+"/PEB_wb_deltares.csv",skiprows=[0,1,2],usecols=["Country","Nation-wide"])	#Exposure bias from older WB DELTARES study
PEB_wb_deltares_older["country"] = replace_with_warning(PEB_wb_deltares_older["Country"],any_to_wb) #Replace with warning is used for columns, for index set_index is needed.

df["pe"]=df["pe"].fillna(PEB_wb_deltares_older.set_index("country").drop(["Country"],axis=1).squeeze()) #Completes with bias from previous study when pov maps not available. squeeze is needed or else it's impossible to fillna with a dataframe
if use_avg_pe:
    df["pe"]=df["pe"].fillna(wavg(df["pe"],df["pop"])) #use averaged pe from global data for countries that don't have PE.
else:
    df["pe"].fillna(0)
pe = df.pop("pe")

###incorporates exposure bias, but only for (riverine) flood and surge, and gets an updated fa for income_cats
fa_hazard_cat = broadcast_simple(fa_guessed_gar,index=income_cats) #fraction of assets affected per hazard and income categories
fa_with_pe = concat_categories(fa_guessed_gar*(1+pe),fa_guessed_gar*(1-df.pov_head*(1+pe))/(1-df.pov_head), index=income_cats)	
# ^ fa_guessed_gar*(1+pe) gives f_p^a and fa_guessed_gar*(1-df.pov_head*(1+pe))/(1-df.pov_head) gives f_r^a. TESTED
fa_with_pe = pd.DataFrame(fa_with_pe).query("hazard in ['flood','surge']").squeeze() #selects just flood and surge
fa_hazard_cat.update(fa_with_pe) #updates fa_guessed_gar where necessary

###gathers hazard ratios
hazard_ratios = pd.DataFrame(fa_hazard_cat)

hazard_ratios["shew"]=broadcast_simple(df.shew, index=hazard_ratios.index)
hazard_ratios["shew"]=hazard_ratios.shew.unstack("hazard").assign(earthquake=0).stack("hazard").reset_index().set_index(event_level+[ "income_cat"]) #shew at 0 for earthquake

if not no_protection:
    #protection at 0 for earthquake and wind
    hazard_ratios["protection"]=1
    hazard_ratios["protection"]=hazard_ratios.protection.unstack("hazard").assign(earthquake=1, wind=1).stack("hazard").reset_index().set_index(event_level)

    hazard_ratios_phl["protection"]=1
    hazard_ratios_phl["protection"]=hazard_ratios_phl.protection.unstack("hazard").assign(earthquake=1, wind=1).stack("hazard").reset_index().set_index(event_level)

hazard_ratios= hazard_ratios.drop("Finland") #because Finland has fa=0 everywhere.

#hazard_ratios_phl = hazard_ratios["Philippines"]

##Protection
if protection_from_flopros: #in this code, this protection is overwritten by no_protection
    minrp = 1/2 #assumes nobody is flooded more than twice a year
    df["protection"]= pd.read_csv(inputs+"/protection_national_from_flopros.csv", index_col="country", squeeze=True).clip(lower=minrp)
else: #assumed a function of the income group
    protection_assumptions = pd.read_csv(inputs+"/protection_level_assumptions.csv", index_col="Income group", squeeze=True)
    df["protection"]=pd.read_csv(inputs+"/income_groups.csv",header =4,index_col=2)["Income group"].dropna().replace(protection_assumptions)
if no_protection:
    p=hazard_ratios.reset_index("rp").rp.min()
    df.protection=p
    if(do_reporting):
        print("PROTECTION IS ",p)

##Data by income categories
cat_info =pd.DataFrame()
cat_info["n"]  = concat_categories(ph,(1-ph),index= income_cats) #number

cp= df["share1"]/df['pov_head']*df["gdp_pc_pp"] #consumption levels, by definition.
cr = (1-df["share1"])/(1-ph)*df["gdp_pc_pp"]

cat_info["c"]       = concat_categories(cp,cr,index= income_cats)
cat_info["social"]  = concat_categories(df.social_p,df.social_r,index= income_cats)	#diversification
cat_info["axfin"] = concat_categories(df.axfin_p,df.axfin_r,index= income_cats)	#access to finance

cat_info = cat_info.dropna()

##Taxes, redistribution, capital
df["tau_tax"],cat_info["gamma_SP"] = social_to_tx_and_gsp(economy,cat_info)	
#computes tau tax and gamma_sp from socail_poor and social_nonpoor. CHECKED!

#here k in cat_info has poor and non poor, while that from capital_data.csv has only k, regardless of poor or nonpoor
cat_info["k"] = (1-cat_info["social"])*cat_info["c"]/((1-df["tau_tax"])*df["avg_prod_k"]) 
#flag

#Exposure
cat_info["fa"] =hazard_ratios.fa.mean(level=["country","income_cat"])

#Vulnerability
cat_info["v"] = concat_categories(vp,vr, index=income_cats)

#access to early warnings
cat_info["shew"] = hazard_ratios.shew.drop("earthquake", level="hazard").mean(level=["country","income_cat"])

if drop_unused_data:
    cat_info = cat_info.drop(["social"],axis=1, errors="ignore").dropna()
    df_in = df.drop(["social_p", "social_r","share1","pov_head", "pe","vp","vr", "axfin_p",  "axfin_r","rating","finance_pre"],axis=1, errors="ignore").dropna()
else :
    df_in = df.dropna()

#df_in = df_in.drop(["shew","v"],axis=1, errors="ignore").dropna()

#Save all data
#hazard_ratios.to_csv(intermediate+"/hazard_ratios.csv",encoding="utf-8", header=True)
#cat_info.to_csv(intermediate+"/cat_info.csv",encoding="utf-8", header=True)
#pd.DataFrame([vp,vr,v], index=["vp","vr","v"]).T.to_csv(intermediate+"/v_pr_fromPAGER_shaved_GAR.csv",encoding="utf-8", header=True)
#fa_guessed_gar.to_csv(intermediate+"/fa_guessed_from_GAR_and_PAGER_shaved.csv",encoding="utf-8", header=True)
#df_in.to_csv(intermediate+"/macro.csv",encoding="utf-8", header=True)

######################################
# ---> Philippines section
#
df_phl = pd.read_excel(PHLinputs+"/PSA_compiled.xlsx",sheetname="data", skiprows=1, index_col=0)#.dropna().squeeze()
df_phl.index.name = "province"
df_phl[["cp","cr","gdp_pc_pp"]]/=1e3

# Pick up columns from df_wb:
df_wb = pd.read_csv(the_file).set_index(economy)
df_phl["axfin_p"] = df_wb["axfin_p"]["Philippines"]
df_phl["axfin_r"] = df_wb["axfin_r"]["Philippines"]

df_phl["urbanization_rate"]=pd.read_csv(inputs+"/wb_data.csv").set_index(economy)["urbanization_rate"]["Philippines"]

df_phl["pi"]                     = reduction_vul       # how much early warning reduces vulnerability
df_phl["rho"]                    = discount_rate       # discount rate
df_phl["shareable"]              = asset_loss_covered  # target of asset losses to be covered by scale up
df_phl["T_rebuild_K"]            = reconstruction_time # Reconstruction time
df_phl["income_elast"]           = inc_elast	       # income elasticity
df_phl["max_increased_spending"] = max_support         # 5% of GDP in post-disaster support maximum, if everything is ready  


df_phl["share1"] = df_phl['cp']*df_phl['pov_head']/df_phl["gdp_pc_pp"] #consumption levels, by definition.
# at this point, df_phl also has ["cp","cr","shewp","shewr"], more than df

# Haven't dissociated these 6 from the previous, but this is particularly important because of "shew"
df_phl["finance_pre"]     = df["finance_pre"]["Philippines"]
df_phl["prepare_scaleup"] = df["prepare_scaleup"]["Philippines"]
df_phl["shew"]            = df["shew"]["Philippines"]
df_phl["rating"]          = df["rating"]["Philippines"]
df_phl["borrow_abi"]      = df["borrow_abi"]["Philippines"]
df_phl["avg_prod_k"]      = df["avg_prod_k"]["Philippines"]

# Income = assets*productivity of capital 
df_phl["assets"]          = df_phl["gdp_pc_pp"]*df_phl["pop"]/df_phl["avg_prod_k"]

# PSA materials file
PSA_vulnerability = get_PSA_building_data(PHLinputs+"/PSA_materials.xlsx")

######
## This is how it was done
## share_phl also references above
#share_phl = pd.DataFrame([share.loc['Philippines']], index=df_phl.index, columns=["fragile","median","robust"])
#
#p_phl = pd.DataFrame(share_phl.cumsum(axis=1), index=df_phl.index, columns=["fragile","median","robust"]).add(-df_phl["pov_head"],axis=0).clip(lower=0)

#poor_phl = (share_phl-p_phl).clip(lower=0)
#rich_phl = share_phl - poor_phl

poor_phl = PSA_vulnerability[PSA_vulnerability.income_cat == 'poor'].drop(['income_cat'],axis=1).multiply(df_phl["pov_head"],axis=0)
rich_phl = PSA_vulnerability[PSA_vulnerability.income_cat == 'nonpoor'].drop(['income_cat'],axis=1).multiply((1-df_phl["pov_head"]),axis=0)

vp_unshaved_phl = (poor_phl*agg_cat_to_v).sum(axis=1, skipna=False)/(df_phl["pov_head"])
vr_unshaved_phl = (rich_phl*agg_cat_to_v).sum(axis=1, skipna=False)/(1-df_phl["pov_head"])
v_unshaved_phl  =  vp_unshaved_phl*df_phl.share1 + vr_unshaved_phl*(1-df_phl["share1"])
v_unshaved_phl.name= "v"
v_unshaved_phl.index.name = "province"

vp_phl = vp_unshaved_phl.copy()
vr_phl = vr_unshaved_phl.copy()
v_phl = v_unshaved_phl.copy()

vp_phl.name = "vp"
vr_phl.name = "vr"
v_phl.name = "v"

#fa is the fraction of asset affected. broadcast_simple, substitute the value in frac_value_destroyed_gar by values in v_unshaved. 
# - Here it assumes that vulnerability for all types of disasters are the same. fa_guessed_gar = exposure/vulnerability
frac_value_destroyed_gar_phl = pd.read_csv(PHLinputs+"/PHL_frac_value_destroyed_gar_completed.csv", index_col=["province", "hazard", "rp"], squeeze=True).dropna()#\delta_K,
df_phl.index.name = "province"

fa_guessed_gar_phl = (frac_value_destroyed_gar_phl/broadcast_simple((v_unshaved_phl),frac_value_destroyed_gar_phl.index)).dropna()

# AIR dataset
AIR_value_destroyed = get_AIR_data(PHLinputs+"/Risk_Profile_Master_With_Population.xlsx","Loss_Results",'all','Agg')
AIR_value_destroyed/=1e3
AIR_value_destroyed.reset_index().set_index('province')
frac_AIR_value_destroyed = (AIR_value_destroyed/df_phl['assets'].squeeze())

fa_guessed_air_phl = (frac_AIR_value_destroyed/broadcast_simple(v_unshaved_phl,AIR_value_destroyed.index)).dropna()

fa_guessed_phl = fa_guessed_air_phl
fa_guessed_phl.name  = "fa"

df_v_phl = vp_phl.to_frame(name="vp")
df_v_phl["vr"] = vr_phl
df_v_phl["v"] = v_phl
df_v_phl.index.name = "province"

df_phl["pe"] = pe["Philippines"]
pe_phl = df_phl.pop("pe")

###incorporates exposure bias, but only for (riverine) flood and surge, and gets an updated fa for income_cats
fa_hazard_cat_phl = broadcast_simple(fa_guessed_phl,index=income_cats)

fa_with_pe_phl = concat_categories(fa_guessed_phl*(1+pe_phl),fa_guessed_phl*(1-df_phl.pov_head*(1+pe_phl))/(1-df_phl.pov_head), index=income_cats)
# ^ fa_guessed_gar*(1+pe) gives f_p^a and fa_guessed_gar*(1-df.pov_head*(1+pe))/(1-df.pov_head) gives f_r^a. TESTED

fa_with_pe_phl = pd.DataFrame(fa_with_pe_phl).query("hazard in ['flood','surge']").squeeze() #selects just flood and surge
fa_hazard_cat_phl.update(fa_with_pe_phl) #updates fa_guessed_gar where necessary

###gathers hazard ratios
hazard_ratios_phl = pd.DataFrame(fa_hazard_cat_phl)

# This sets early warning access to 60% for all provinces 
hazard_ratios_phl["shew"]=broadcast_simple(df_phl.shew, index=hazard_ratios_phl.index)

# This block sets early warning access to province- and income-specific values
hazard_ratios_phl = hazard_ratios_phl.reset_index().set_index('province')
hazard_ratios_phl.ix[hazard_ratios_phl.income_cat == "poor","shew"] = df_phl.shewp
hazard_ratios_phl.ix[hazard_ratios_phl.income_cat == "nonpoor","shew"] = df_phl.shewr
hazard_ratios_phl = hazard_ratios_phl.reset_index().set_index(['province','hazard','rp','income_cat'])

# No early warning for earthquakes
hazard_ratios_phl["shew"]=hazard_ratios_phl.shew.unstack("hazard").assign(earthquake=0).stack("hazard").reset_index().set_index(["province", "hazard", "rp", "income_cat"])

# Either pick up single value at country level (20.0 is from gRIMM, JC uses 1.0)
df_phl["protection"] = 1#df["protection"]["Philippines"]    
# or use input file from PHL-RIMM (Adrien)
#df_phl["protection"] = pd.read_csv(PHLinputs+"/PHL_protection.csv", index_col="province", squeeze=True).clip(lower=minrp)
#df_phl["protection"] = df_phl["protection"].fillna(df["protection"]["Philippines"])# if no provincial data, use national number (20.0)

##Data by income categories
cat_info_phl = pd.DataFrame()
cat_info_phl["n"]  = concat_categories(df_phl["pov_head"],(1-df_phl["pov_head"]),index= income_cats) #number

cp_phl = df_phl["cp"] 
cr_phl = df_phl["cr"]

cat_info_phl["c"] = concat_categories(cp_phl,cr_phl,index= income_cats)
cat_info_phl["social"] = concat_categories(df_phl.social_p, df_phl.social_r, index=income_cats) #diversification
cat_info_phl["axfin"] = concat_categories(df_phl.axfin_p, df_phl.axfin_r, index=income_cats) #access to finance

cat_info_phl = cat_info_phl.dropna()

# national average GDP per cap
df_phl['gdp_pc_pp_nat'] = (df_phl['gdp_pc_pp']*df_phl['pop']).sum(axis=0)/df_phl['pop'].sum(axis=0)

##Taxes, redistribution, capital
df_phl["tau_tax"],cat_info_phl["gamma_SP"] = social_to_tx_and_gsp('province',cat_info_phl)

#here k in cat_info has poor and non poor, while that from capital_data.csv has only k, regardless of poor or nonpoor
cat_info_phl["k"] = (1-cat_info_phl["social"])*cat_info_phl["c"]/((1-df_phl["tau_tax"])*df_phl["avg_prod_k"]) 

#Exposure
cat_info_phl["fa"] =hazard_ratios_phl.fa.mean(level=["province","income_cat"])

#Vulnerability
cat_info_phl["v"] = concat_categories(vp_phl,vr_phl, index=income_cats)

#access to early warnings
cat_info_phl["shew"] = hazard_ratios_phl.shew.drop("earthquake", level="hazard").mean(level=["province","income_cat"])

if drop_unused_data:
    cat_info_phl = cat_info_phl.drop(["social"],axis=1, errors="ignore").dropna()
    df_in_phl = df_phl.drop(["social_p", "social_r","share1","pov_head", "pe","vp","vr", "axfin_p",  "axfin_r","rating","finance_pre"],axis=1, errors="ignore").dropna()
else :
    df_in_phl = df_phl.dropna()

df_in_phl = df_in_phl.drop(["shew","v"],axis=1, errors="ignore").dropna()

# PHL: save all data
cat_info_phl.to_csv(intermediate+"/PHL_cat_info.csv",encoding="utf-8", header=True)
hazard_ratios_phl.to_csv(intermediate+"/PHL_hazard_ratios.csv",encoding="utf-8", header=True)
df_v_phl.to_csv(intermediate+"/PHL_v_pr_fromPAGER_shaved_GAR.csv",encoding="utf-8", header=True)
fa_guessed_phl.to_csv(intermediate+"/PHL_fa_guessed_from_GAR_and_PAGER_shaved.csv",encoding="utf-8", header=True)
df_in_phl.to_csv(intermediate+"/PHL_macro.csv",encoding="utf-8", header=True)
