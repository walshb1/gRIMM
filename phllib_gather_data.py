import pandas as pd
from pandas_helper import get_list_of_index_names, broadcast_simple, concat_categories

def get_AIR_data(fname,sname,keep_sec,keep_per):
    # AIR dataset province code to province name
    AIR_prov_lookup = pd.read_excel(fname,sheetname='Lookup_Tables',usecols=['province_code','province'],index_col='province_code')
    AIR_prov_lookup = AIR_prov_lookup['province'].to_dict()

    AIR_prov_corrections = {'Tawi-Tawi':'Tawi-tawi',
                            #'Metropolitan Manila':'Manila',
                            'Davao del Norte':'Davao',
                            #'Batanes':'Batanes_off',
                            'North Cotabato':'Cotabato'}
    
    # AIR dataset peril code to peril name
    AIR_peril_lookup_1 = pd.read_excel(fname,sheetname="Lookup_Tables",usecols=['perilsetcode','peril'],index_col='perilsetcode')
    AIR_peril_lookup_1 = AIR_peril_lookup_1['peril'].dropna().to_dict()
    AIR_peril_lookup_2 = {'EQ':'earthquake', 'HUSSPF':'typhoon', 'HU':'wind', 'SS':'surge', 'PF':'flood'}

    AIR_value_destroyed = pd.read_excel(fname,sheetname="Loss_Results",
                                        usecols=['perilsetcode',"province","Perspective","Sector","EP10","EP25","EP30","EP50","EP100","EP200","EP250","EP500","EP1000"]).squeeze()
    AIR_value_destroyed.columns=['hazard','province','Perspective','Sector',10,25,30,50,100,200,250,500,1000]

    # Change province code to province name
    #AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['hazard','Perspective','Sector'])
    AIR_value_destroyed["province"].replace(AIR_prov_lookup,inplace=True)
    AIR_value_destroyed["province"].replace(AIR_prov_corrections,inplace=True) 
    #AIR_prov_corrections

    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index('province')
    AIR_value_destroyed = AIR_value_destroyed.drop('All Provinces')

    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['hazard','province','Perspective','Sector'])
    AIR_value_destroyed = AIR_value_destroyed.drop(['index'],axis=1, errors="ignore")

    # Stack return periods column
    AIR_value_destroyed.columns.name='rp'
    AIR_value_destroyed = AIR_value_destroyed.stack()

    # Name values
    #AIR_value_destroyed.name='v'

    # Choose only Sector = 0 (Private Assets) 
    # --> Alternative: 15 = All Assets (Private + Govt (16) + Emergency (17))
    sector_dict = {'Private':0, 'private':0,
                   'Government':16, 'government':16,
                   'Emergency':17, 'emergency':17,
                   'All':15, 'all':15}
    
    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['Sector'])
    AIR_value_destroyed = AIR_value_destroyed.drop([iSec for iSec in range(0,30) if iSec != sector_dict[keep_sec]])
    
    # Choose only Perspective = Occurrence ('Occ') OR Aggregate ('Agg')
    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['Perspective'])
    AIR_value_destroyed = AIR_value_destroyed.drop([iPer for iPer in ['Occ', 'Agg'] if iPer != keep_per])
    
    # Map perilsetcode to perils to hazard
    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['hazard'])
    AIR_value_destroyed = AIR_value_destroyed.drop(-1)

    # Drop Sector and Perspective columns
    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['province','hazard','rp'])
    AIR_value_destroyed = AIR_value_destroyed.drop(['Sector','Perspective'],axis=1, errors="ignore")
    
    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index('province')
    AIR_value_destroyed["hazard"].replace(AIR_peril_lookup_1,inplace=True)
    AIR_value_destroyed["hazard"].replace(AIR_peril_lookup_2,inplace=True)
    
    # Keep only earthquake (EQ) and tsunami (HUSSPF)
    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['hazard'])
    AIR_value_destroyed = AIR_value_destroyed.drop(['typhoon'])    

    AIR_value_destroyed = AIR_value_destroyed.reset_index().set_index(['province','hazard','rp'])

    AIR_value_destroyed = AIR_value_destroyed.sort_index().squeeze()

    return AIR_value_destroyed

def get_PSA_building_data(fname):
    PSA_roof_poor    = pd.read_excel(fname,sheetname='Prop_Roof_Poor',index_col='province',skiprows=1)
    PSA_roof_nonpoor = pd.read_excel(fname,sheetname='Prop_Roof_Non-poor',index_col='province',skiprows=1)
    PSA_wall_poor    = pd.read_excel(fname,sheetname='Prop_Wall_Poor',index_col='province',skiprows=1)
    PSA_wall_nonpoor = pd.read_excel(fname,sheetname='Prop_Wall_Non-poor',index_col='province',skiprows=1)

    PSA_vulnerability = pd.DataFrame(index=PSA_roof_poor.index)

    PSA_vulnerability['poor'] = 0
    PSA_vulnerability['nonpoor'] = 0
    PSA_vulnerability.columns.name = 'income_cat'

    PSA_vulnerability = PSA_vulnerability.stack().reset_index().set_index('province')
    PSA_vulnerability = PSA_vulnerability.drop([0],axis=1)

    # Nonpoor
    PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'nonpoor','fragile'] = (PSA_wall_nonpoor['wall_salvaged'] + PSA_roof_nonpoor['roof_salvaged'] 
                                                                                 + PSA_wall_nonpoor['wall_mixed_salvaged'] + PSA_roof_nonpoor['roof_mixed_salvaged'])/2   
    PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'nonpoor','median'] = (PSA_wall_nonpoor['wall_light'] + PSA_roof_nonpoor['roof_light']
                                                                                + PSA_wall_nonpoor['wall_mixed_light'] + PSA_roof_nonpoor['roof_mixed_light'])/2    
    PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'nonpoor','robust'] = (PSA_wall_nonpoor['wall_strong'] + PSA_roof_nonpoor['roof_strong']
                                                                                + PSA_wall_nonpoor['wall_mixed_strong'] + PSA_roof_nonpoor['roof_mixed_strong'])/2

    #PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'nonpoor','fragile'] = 0
    #PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'nonpoor','median'] = 0
    #PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'nonpoor','robust'] = 1

    # Poor
    PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'poor','fragile'] = (PSA_wall_poor['wall_salvaged'] + PSA_roof_poor['roof_salvaged'] 
                                                                              + PSA_wall_poor['wall_mixed_salvaged'] + PSA_roof_poor['roof_mixed_salvaged'])/2   
    PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'poor','median'] = (PSA_wall_poor['wall_light'] + PSA_roof_poor['roof_light']
                                                                             + PSA_wall_poor['wall_mixed_light'] + PSA_roof_poor['roof_mixed_light'])/2    
    PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'poor','robust'] = (PSA_wall_poor['wall_strong'] + PSA_roof_poor['roof_strong']
                                                                             + PSA_wall_poor['wall_mixed_strong'] + PSA_roof_poor['roof_mixed_strong'])/2


    #PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'poor','fragile'] = 0
    #PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'poor','median'] = 0
    #PSA_vulnerability.ix[PSA_vulnerability.income_cat == 'poor','robust'] = 1

    return PSA_vulnerability
