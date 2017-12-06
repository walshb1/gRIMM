from lib_gather_data import social_to_tx_and_gsp, broadcast_simple

def get_pol_opt_str(optionFee,optionPDS,is_local_welfare,opt_social,opt_shew,opt_rshar,opt_insured,opt_exposure):
    
    POdir = ''
    if is_local_welfare == False:
        POdir = 'gdpNTL'
    else: POdir = 'gdpLOC'

    POstr = '_'+optionFee+'_'+optionPDS
    
    if (opt_social != None or opt_shew != None or opt_rshar != None or opt_insured != 25 or opt_exposure != None): 
        POdir += '/options'
        POstr += '_'
    
    if opt_social != None:
        POstr += 'so'+str(opt_social)
    if opt_shew != None:
        POstr += 'ew'+str(opt_shew)
    if opt_rshar != None:
        POstr += 'rs'+str(opt_rshar)
    if opt_insured != 25:
        POstr += 'in'+str(opt_insured)
    if opt_exposure != None:
        POstr += 'ex'+str(opt_exposure)

    POstr += '.csv'

    return POdir, POstr

def policy_option_exposure(cat_info,hazard_ratios,event_level,opt_exposure,del_v=0.05):
    if opt_exposure != None:

        ## Calculate value of 5% reduction in total vulnerability & attribute to either poor or nonpoor 
        tmp_cat_info = cat_info.reset_index().set_index('province')

        tmp_cat_info['del_k'] = tmp_cat_info['k'].sum(level='province')*del_v
        tmp_cat_info['del_fa'] = tmp_cat_info['del_k'].divide(tmp_cat_info['k'])
        tmp_cat_info.ix[(tmp_cat_info.income_cat==opt_exposure),'fa'] -= tmp_cat_info.ix[(tmp_cat_info.income_cat==opt_exposure),'del_fa']
        tmp_cat_info['fa'] = tmp_cat_info['fa'].clip(0.0,0.9)
        
        # Reset indices and drop new columns
        tmp_cat_info = tmp_cat_info.reset_index().set_index(['province','income_cat'])
        cat_info = tmp_cat_info.drop(['del_k','del_fa'],axis=1)

        ## Now apply the same calculations to hazard_ratios
        tmp_hazard_ratios = hazard_ratios.reset_index().set_index(['province','income_cat'])

        tmp_hazard_ratios['del_fa'] = broadcast_simple(tmp_cat_info['del_fa'],index=tmp_hazard_ratios.index)
        
        tmp_hazard_ratios = tmp_hazard_ratios.reset_index().set_index('province')        

        tmp_hazard_ratios.ix[(tmp_hazard_ratios.income_cat==opt_exposure),'fa'] -= tmp_hazard_ratios.ix[(tmp_hazard_ratios.income_cat==opt_exposure),'fa']*tmp_hazard_ratios.ix[(tmp_hazard_ratios.income_cat==opt_exposure),'del_fa']

        # Reset indices and drop new columns
        tmp_hazard_ratios = tmp_hazard_ratios.drop(['del_fa'],axis=1).reset_index().set_index(['province','hazard','rp','income_cat'])
        hazard_ratios = tmp_hazard_ratios

    return cat_info,hazard_ratios

def policy_option_benefits(cat_info,opt_benefits):
    if opt_benefits != None:
        return cat_info

def policy_option_social(macro,cat_info,opt_social):
    # This increases social protection by percentage specified by opt_social

    if opt_social != None:

        macro['social_p']*=(1.0+float(opt_social)/100)
        macro.social_p = macro.social_p.clip(0.0,1.0)

        macro['social_r']*=(1.0+float(opt_social)/100)
        macro.social_r = macro.social_r.clip(0.0,1.0)

        cat_info['social']*=(1.0+float(opt_social)/100)
        cat_info.social = cat_info.social.clip(0.0,1.0)

        macro["tau_tax"],cat_info["gamma_SP"] = social_to_tx_and_gsp('province',cat_info)

    return macro, cat_info

def policy_option_shew(macro,hazard_ratios,event_level,opt_shew):
    # This sets early warning to number specified by opt_shew

    if opt_shew != None:
            
        macro.shewp = float(opt_shew)/100
        
        macro.shewr = float(opt_shew)/100
        
        #shew always 0 for earthquakes
        hazard_ratios.shew = float(opt_shew)/100
        hazard_ratios['shew']=hazard_ratios.shew.unstack("hazard").assign(earthquake=0).stack("hazard").reset_index().set_index(event_level+[ "income_cat"]) 

    return macro,hazard_ratios

def policy_option_rshar(dK,opt_rshar):

    if opt_rshar != None:
        dK*=(1.0-float(opt_rshar)/100)
    
    return dK
