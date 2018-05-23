from pandas_helper import *
#from res_ind_lib import *
import os, time

def apply_policy(m_,c_,h_, policy_name=None, policy_opt=None, a_=None,verbose=True):
    """Choses a policy by name, applies it to m,c,and/or h, and returns new values as well as a policy description"""

    #duplicate inputes
    m=m_.copy(deep=True)
    c=c_.copy(deep=True)
    h=h_.copy(deep=True)
    a=a_ #dictionary, do not attempt to deep copy
    desc = ''

    if policy_name is None:
        desc = "Baseline"

    elif policy_name == 'borrow_abi':
        m.borrow_abi = 2
        desc = 'Increase borrow_abi to 2 for all countries'

    # Pov reduction
    elif policy_name=="kp":
        c.k = c.k.unstack().assign(poor=lambda df:df.poor*1.1).stack()
        desc = "Increase\nincome of the\npoor 10%"    # Pov reduction

    elif policy_name=="pov_head":
        c.n = c.n.unstack().assign(poor=.18, nonpoor=.82).stack()
        desc = "Reduce poverty from 20% to 18%"

    #Borrow abi
    elif policy_name=="borrow_abi":
        m.borrow_abi = m.borrow_abi.clip(lower=1)
        desc = "Develop contingent finance and reserve funds"

    #Scale up abi
    elif policy_name=="prepare_scaleup":
        m.prepare_scaleup = 1
        desc = "Make social protection scalable after a shock"

    #Early warnings to 1, except for earthquake
    elif policy_name=="shew":
        h.shew =1
        h.shew=h.shew.unstack("hazard").assign(earthquake=0).stack("hazard").reset_index().   set_index(event_level+[ "income_cat"])
        desc = "Universal\naccess to early\nwarnings"

    #reconstruction to X years
    elif policy_name=="T_rebuild_K":
        m.T_rebuild_K = policy_opt
        desc = "Accelerate reconstruction (by some%)"

    #social_p needs to be at least 50%
    elif policy_name=="social_p":

        m,c=clip_social_p(m,c,fun=lambda x: x.clip(lower=.33)   )
        # )
        desc = "Increase social\ntransfers to poor\npeople to at\nleast 33%"

    elif policy_name=="axfin":
        c.axfin=1
        desc = "Universal\naccess to\nfinance"

    #vpoor = vnonpoor
    elif policy_name=="vpvr":
        c.v = c.v.unstack().assign(poor=lambda x:x.nonpoor).stack()
        desc = "Make poor people's assets as resistant as nonpoor people's assets"

    #30% or poor people see their v reduced 30% (not 10pts!!)
    elif policy_name=="vp":
        n = c.n.unstack().poor
        dv = .3 #reduction in v
        f =.05 #fractionof nat pop would get the reduction
        c.v = c.v.unstack().assign(poor=lambda df:(df.poor*(1-dv*f/n))).stack().clip(lower=0)
        desc = "Reduce asset\nvulnerability\n(by 30%) of\npoor people\n(5% of the population)"

    #Borrow abi
    elif policy_name=="bbb_incl":
        m.borrow_abi = policy_opt

    #reconstruction to X years
    elif policy_name=="bbb_fast":
        m.T_rebuild_K = policy_opt


    #previously affected people see their v reduced 30%
    elif 'bbb' in policy_name:
        #h = pd.merge(h.reset_index(),c['v'].reset_index(),on=['country','income_cat'])

        if policy_name=="bbb":
            dv = policy_opt #reduction in v
            c.v = c.v*(1-dv)
            desc = "Reduce asset\nvulnerability\n(by 30%)"

        elif policy_name=="bbb_uncor":
            disaster_years = 20
            dv = policy_opt #reduction in v

            for i in range(disaster_years):
                h.loc[h.rp==1,'v'] *= h.fa*(1-dv)+(1-h.fa)
                h.loc[h.rp!=1,'v'] *= 1-(1/h.rp.astype('int'))*(h.fa*(1-dv)+(1-h.fa))

        elif policy_name=="bbb_cor":
            disaster_years = 20
            dv = policy_opt #reduction in v

            for i in range(disaster_years):
                h.loc[h.rp==1,'v'] *= (1-dv)
                h.loc[h.rp!=1,'v'] *= 1-(1/h.rp.astype('int'))*(1-dv)

        elif policy_name=="bb_standard":
            disaster_years = 20
            h.fa *= (1-h.fa)**disaster_years

        elif policy_name=='bbb_50yrstand':
            n_years = 20
            h = h.reset_index()
            #h['p_annual_occur'] = (1./h.rp)
            #h['exp_val'] = n_years*h['p_annual_occur']
            # ^ expectation value of binomial dist is np
            #h['fa_scale_fac'] = (1.-h['fa'])**h['exp_val']
            #h['cum_fa_scale_fac'] = h.groupby(['country','hazard','income_cat'])['fa_scale_fac'].transform('prod')
            # These 2 approaches (above and below) produce near-identical (within 0.1%) results.
            #h['dfa_1yr'] = (1.-h.fa/h.rp)
            # scale_fac on fa, including probability that the event occurs in a single year
            # --> but this doesn't include the fact that fa is going down each year...

            h['tmp_fa'] = h['fa'].copy()
            for iyr in range(n_years): h['tmp_fa'] *= (1.-h['tmp_fa']/h['rp'])
            # calculate scale fac on fa after n_years
            # --> updates tmp_fa each step of the way, so this is recursive

            h['dfa'] = h['tmp_fa']/h['fa']
            h['cum_dfa'] = h.groupby(['country','hazard','income_cat'])['dfa'].transform('prod')
            # cum_scale_fac includes all rps and their probabilities...
            # --> If a hh is affected by the 1-year or the 2000-year event, it rebuilds in such a way that it is invulnerable to the 50-year event

            h.loc[h.rp<=50,'fa'] *= h.loc[h.rp<=50,'cum_dfa']

            h = h.drop(['dfa','tmp_fa','cum_dfa'],axis=1)
            #print(h.head())

        elif policy_name=='bbb_complete':
            m.borrow_abi = 1
            m.T_rebuild_K = policy_opt
            n_years = 20
            h = h.reset_index()

            h['tmp_fa'] = h['fa'].copy()
            for iyr in range(n_years): h['tmp_fa'] *= (1.-h['tmp_fa']/h['rp'])

            h['dfa'] = h['tmp_fa']/h['fa']
            h['cum_dfa'] = h.groupby(['country','hazard','income_cat'])['dfa'].transform('prod')
            h.loc[h.rp<=50,'fa'] *= h.loc[h.rp<=50,'cum_dfa']

            h = h.drop(['dfa','tmp_fa','cum_dfa'],axis=1)
            #print(h.head())
        #build back better & faster - previously affected people see their v reduced 50%, T_rebuild is reduced too
        elif policy_name=="bbbf":
            m.T_rebuild_K = 3-(policy_opt*5)
            dv = policy_opt #reduction in v
            c.v = c.v*(dv-1)

        h = h.reset_index().set_index(['country','hazard','rp','income_cat']).drop('index',axis=1)


    elif policy_name=="20dK":
        model        = os.getcwd()
        intermediate = model+'/intermediate/'
        economy="country"
        #print "OK up to here1"
        the_bbb_file= intermediate+"K_inputs.csv"
        #print "OK up to here1.5"
        df_bbb= pd.read_csv(the_bbb_file).set_index(economy)
        #print "OK up to here2"
        df_bbb["20dKtot"]= pd.read_csv(intermediate+"K_inputs.csv").set_index(economy)["20dKtot"] #read data
        df_bbb["K_stock"]= pd.read_csv(intermediate+"K_inputs.csv").set_index(economy)["K"]
        #print "OK up to here3"
        twdKtot = df_bbb["20dKtot"]
        K_stock = df_bbb["K_stock"]
        dv = policy_opt #reduction in v
        c.v = (twdKtot/K_stock)*(1-dv)*c.v + (1 - twdKtot/K_stock)*c.v
        #print K_stock

    elif policy_name=="dK_rp20":
        model        = os.getcwd()
        intermediate = model+'/intermediate/'
        economy="country"
        the_bbb_file= intermediate+"K_inputs.csv"
        df_bbb= pd.read_csv(the_bbb_file).set_index(economy)
        df_bbb["dKtot_rp20"]= pd.read_csv(intermediate+"K_inputs.csv").set_index(economy)["dKtot_rp20"] #read data
        df_bbb["K_stock"]= pd.read_csv(intermediate+"K_inputs.csv").set_index(economy)["K"]
        dK_rp20 = df_bbb["dKtot_rp20"]
        K_stock = df_bbb["K_stock"]
        dv = policy_opt #reduction in v
        c.v = (dK_rp20/K_stock)*(1-dv)*c.v + (1 - dK_rp20/K_stock)*c.v

    #10% or nonpoor people see their v reduced 30%
    elif policy_name=="vr":
        n = c.n.unstack().nonpoor
        dv = .3 #reduction in v
        f =.05 #fractionof nat pop would get the reduction
        c.v = c.v.unstack().assign(nonpoor=lambda x:(x.nonpoor*(1-dv*f/n))).stack().clip(lower=0)
        desc = "Reduce asset\nvulnerability\n(by 30%) of\nnonpoor people\n(5% of the population)"

    #10% or poor people see their fA reduced 10%
    elif policy_name=="fap":
        n = 0.2
        dfa = .05 #reduction in fa

        h["n"] = h.assign(n=1).n.unstack().assign(poor=0.2,nonpoor=0.8).stack()
        fa_event = agg_to_event_level(h,"fa")

        h = h.drop("n",axis=1)

        h.fa = h.fa.unstack().assign(poor=lambda x:(x.poor-dfa*fa_event/n)).stack().clip(lower=0)
        desc = "Reduce exposure\nof the poor by 5%\nof total exposure"



    #10% or NONpoor people see their fA reduced 10%
    elif policy_name=="far":
        n = 0.8
        dfa =.05 #fractionof nat pop would get the reduction

        h["n"] = h.assign(n=1).n.unstack().assign(poor=0.2,nonpoor=0.8).stack()
        fa_event = agg_to_event_level(h,"fa")

        h.fa = h.fa.unstack().assign(nonpoor=lambda x:(x.nonpoor-dfa*fa_event/n)).stack().clip(lower=0)
        desc =  "Reduce\nexposure of the nonpoor by 5%\nof total exposure"

    #Exposure equals to nonpoor exposure (mind that exposure in cat_info is OVERWRITTEN by exposure in h)
    elif policy_name=="fapfar":
        h.fa = h.fa.unstack().assign(poor=lambda x:x.nonpoor).stack()
        desc = "Make poor people's exposure the same as the rest of population"

    elif policy_name=="prop_nonpoor":
        #a.update(optionPDS = "prop_nonpoor", optionT="perfect",optionB="unlimited",optionFee="insurance_premium", share_insured=.25)
        desc = "Develop market\ninsurance\n(nonpoor people)"

    elif policy_name=="prop_nonpoor_lms":
        #a.update(optionPDS = "prop_nonpoor_lms", optionT="prop_nonpoor_lms",optionB="unlimited",optionFee="insurance_premium", share_insured=.5)
        desc = "Develop market insurance (25% of population, only nonpoor)"


    elif policy_name=="PDSpackage":
        m,c,h,a,desc = apply_policy(m,c,h,a,"borrow_abi")
        m,c,h,a,desc = apply_policy(m,c,h,a,"prepare_scaleup")

        desc = "Postdisaster\nsupport\npackage"

    elif policy_name=="ResiliencePackage":
        m,c,h,a,desc = apply_policy(m,c,h,a,"PDSpackage")
        m,c,h,a,desc = apply_policy(m,c,h,a,"axfin")
        m,c,h,a,desc = apply_policy(m,c,h,a,"T_rebuild_K")
        m,c,h,a,desc = apply_policy(m,c,h,a,"social_p")
        m,c,h,a,desc = apply_policy(m,c,h,a,"prop_nonpoor_lms")
        desc = "Resilience package"


    elif policy_name=="ResiliencePlusEW":
        m,c,h,a,desc = apply_policy(m,c,h,a,"ResiliencePackage")
        m,c,h,a,desc = apply_policy(m,c,h,a,"shew")

        desc = "Resilience Package + Early Warning Package"

    elif policy_name=="Asset_losses" :
        m,c,h,a,desc = apply_policy(m,c,h,a,"fap")
        m,c,h,a,desc = apply_policy(m,c,h,a,"far")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vp")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vr")
        m,c,h,a,desc = apply_policy(m,c,h,a,"shew")

        desc = "Asset losses package "

    elif policy_name=="Asset_losses_no_EW":
        m,c,h,a,desc = apply_policy(m,c,h,a,"fap")
        m,c,h,a,desc = apply_policy(m,c,h,a,"far")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vp")
        m,c,h,a,desc = apply_policy(m,c,h,a,"vr")
        desc = "Asset losses package (excluding early warnings)"

    elif policy_name=="":
        pass

    if verbose:
        print(desc)

    return m,c,h, a, desc



def clip_social_p(m,c,fun=lambda x: x.clip(lower=.50)   ) :
        """Compute social p from cat_info (c) and macro (m).
        Then changes social p to something applying fun
            for instance fun=lambda x:.3333 will set social_p at .3333
            fun = lambda x: x.clip(lower=.50) gets social p at least at 50%
        """

        m = m.copy(deep=True)
        c = c.copy(deep=True)

        #############
        #### preparation

        #current conso and share of average transfer
        cp  = c.c.ix[:,"poor"]
        gsp = c.gamma_SP.ix[:,"poor"]
        cp.head()

        #social_p
        cur_soc_sh = gsp* m.gdp_pc_pp  *m.tau_tax /cp
        cur_soc_sh.head()

        #social_p needs to be at least 50%
        obj_soc_sh  = fun(cur_soc_sh)
        # obj_soc_sh.sample(10)

        # increase of transfer for poor people
        money_needed = (obj_soc_sh*(1-cur_soc_sh)/(1-obj_soc_sh)-cur_soc_sh)*cp
        money_needed.head()

        #financing this transfer with a tax on the whole population
        nu_tx = (m.gdp_pc_pp*m.tau_tax+money_needed*c.n.ix[:,"poor"])/m.gdp_pc_pp
        nu_tx.head();

        #increasing the share of avg transfer that goes to poor
        nu_gsp = (money_needed+cur_soc_sh*cp)/(m.gdp_pc_pp*nu_tx)

        #balancing with less for nonpoor
        nu_gs = (1-0.2*nu_gsp)/0.8
        nu_gs;

        #double checking that that the objectife of 50% at least has been met
        # new_soc_sh = nu_gsp* m.gdp_pc_pp  *nu_tx /(cp+money_needed)
        # ((new_soc_sh-obj_soc_sh)**2).sum()

        #updating c and m
        c.gamma_SP = concat_categories(nu_gsp,nu_gs,index=income_cats);
        m.tau_tax = nu_tx

        return m,c
