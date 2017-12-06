from pylab import *
import csv
import prettyplotlib as ppl
import matplotlib.patches as pts
from matplotlib import rc
from matplotlib import colors
from textwrap import wrap
from collections import OrderedDict
import os
rc('text', usetex=False)

import pandas as pd

import scipy.stats as stats
import matplotlib.mlab as mlab

#Aesthetics
import seaborn as sns
import brewer2mpl as brew
from matplotlib import colors

def_pal = sns.color_palette()

def categorize_GDP(df):
    array = df['pop'].astype('float')*df['gdp_pc_pp'].astype('float')
    df_gdp  = pd.DataFrame([return_bin(array,iGDP) for iGDP in array],index=df.index)
    df_gdpl = pd.DataFrame([return_label(array,iGDP) for iGDP in array],index=df.index)

    #df_gdpl2 = []
    #for iEconVal in df_gdpl:
    #    if iEconVal not in df_gdpl2:
    #        df_gdpl2.append(iEconVal)
    #    else:
    #        df_gdpl2.append(None)

    return df_gdp, df_gdpl

def return_bin(array,iGDP):
    if iGDP >= np.percentile(array,75): return 1600
    if iGDP >= np.percentile(array,50): return 800
    if iGDP >= np.percentile(array,25): return 400
    return 200

def return_label(array,iGDP):
    if iGDP >= np.percentile(array,75): return '4th quartile'
    if iGDP >= np.percentile(array,50): return '3rd quartile'
    if iGDP >= np.percentile(array,25): return '2nd quartile'
    return '1st quartile'

def plot_trendline(colX,colY):
    tl_xvals = np.linspace(min(colX), max(colX), 10)
    
    r, p = stats.pearsonr(colX,colY)
    m, b = np.polyfit(colX,colY, 1)
    tl = b + (m*tl_xvals)
    plt.plot(tl_xvals,tl,marker=None, linestyle='-')

    annotate(r'r$^2$ = '+str(round(r**2,2)),xy=(0.9,0.5),xycoords='axes fraction',ha='right')

    return True

def do_norm_fit(plotA,data_to_fit,bns,col):
    (mu, sigma) = stats.norm.fit(data_to_fit)
    fit = mlab.normpdf( bins, mu, sigma)
    plotA.plot(bins,fit, '--', color=col,linewidth=2)

def do_ray_fit(plotA,data_to_fit,bns,col):
    # Generate Rayleigh distribution
    param = stats.rayleigh.fit(data_to_fit)

    ray_fitted = stats.rayleigh.pdf(bns,loc=param[0],scale=param[1])

    plotA.plot(bns,ray_fitted,'--',color=col)

    return True

def isInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False
    except TypeError:
        return False
             
def isFloat(string,ndec=10):
    try:
        float(string)
        return round(float(string),ndec)
    except ValueError:
        return string

def getcol(array, index):
    if isInt(index):
        return [xrow[index] for xrow in array]
    else:
        return [[xrow[aCol] for aCol in index] for xrow in array]

def getarr(array, index):
    return np.array([xrow[index] for xrow in array])

def read_file(fname):
    head = {}
    df = []

    with open(fname) as f:
        reader = csv.reader(f)
        
        for idx, irow in enumerate(reader):

            irow = str(irow).replace('[','').replace(']','').replace("'",'').replace(' ','').split(',')

            for jdx, jcol in enumerate(irow):
                irow[jdx] = isFloat(jcol)
    
            if idx == 0:
                for jdx, jcol in enumerate(irow):
                    head[jcol] = jdx
            
            else: df.append(irow)  

    return head, df

# read in output file
cdir   = os.getcwd()          # current directory
dbdir  = cdir+'/debug_plots/' # plots go here
shewdir = dbdir+'/option_shew/'
rshardir = dbdir+'/option_risk_sharing/'
social05dir = dbdir+'/option_social/05/'
social10dir = dbdir+'/option_social/10/'
social15dir = dbdir+'/option_social/15/'
expdir = dbdir+'/option_exposure/poor/'
exnpdir = dbdir+'/option_exposure/nonpoor/'
if not os.path.exists(dbdir): os.makedirs(dbdir)
if not os.path.exists(shewdir): os.makedirs(shewdir)
if not os.path.exists(rshardir): os.makedirs(rshardir)
if not os.path.exists(social05dir): os.makedirs(social05dir)
if not os.path.exists(social10dir): os.makedirs(social10dir)
if not os.path.exists(social15dir): os.makedirs(social15dir)
if not os.path.exists(expdir): os.makedirs(expdir)
if not os.path.exists(exnpdir): os.makedirs(exnpdir)

loc_nat = 'gdpLOC'
for anOption in [['output/'+loc_nat+'/PHL_results_tax_no.csv',dbdir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_ew100.csv',shewdir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_rs30.csv',rshardir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_so5.csv',social05dir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_so10.csv',social10dir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_so15.csv',social15dir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_expoor.csv',expdir],
                 ['output/'+loc_nat+'/options/PHL_results_tax_no_exnonpoor.csv',exnpdir]]:
                 
    res_head, res_df = read_file(anOption[0])

    print('\n Reading in '+anOption[0])

    #macro_head, macro_df = read_file('intermediate/PHL_macro.csv')
    #print(macro_head)

    plot_pairs = [['gdp_pc_pp','risk'],
                  ['gdp_pc_pp','resilience'],
                  ['gdp_pc_pp','risk_to_assets'],
                  ['gdp_pc_pp','pov_head'],
                  ['gdp_pc_pp','cp'],
                  ['gdp_pc_pp','cr'],
                  ['gdp_pc_pp','protection'],
                  ['gdp_pc_pp','dWpc_currency'],
                  ['pov_head','resilience'],
                  ['pov_head','risk'],
                  ['pov_head','risk_to_assets'],
                  ['delta_W','dWpc_currency'],
                  ['risk','resilience'],
                  ['risk','risk_to_assets'],
                  ['resilience','risk_to_assets'],
                  ['gdp_pc_pp','v'],
                  ['gdp_pc_pp','dk'],
                  ['gdp_pc_pp','fa'],
                  ['gdp_pc_pp','dk'],
                  ['gdp_pc_pp','social_p'],
                  ['social_p','resilience'],
                  ['cp','cr'],
                  ['gini','resilience'],
                  ['gini','risk_to_assets'],
                  ['gini','risk']]

    plot_dim = {'resilience':[0.5,1],
                'pov_head':[0,1]
                #'delta_W':[0,0.0002],
                #'risk':[0.1,0.2],
                #'fa':[0.08,0.12]
                }

    for ipair in plot_pairs:
        plt.cla()

        if ipair[0] == 'gini':

            gap = getarr(res_df,res_head['cr'])-getarr(res_df,res_head['cp'])

            gini_pop = getarr(res_df,res_head['pop'])  
            gini_npoor = getarr(res_df,res_head['pov_head'])*gini_pop
            gini_nrich = (1-getarr(res_df,res_head['pov_head']))*gini_pop
                
            gini_poor_pc = getarr(res_df,res_head['cp'])
            gini_rich_pc = getarr(res_df,res_head['cr'])
            gini_gdp_pc = getarr(res_df,res_head['gdp_pc_pp'])
        
            gini_dnm = 0.5*gini_gdp_pc*gini_pop
            gini_num = gini_dnm - (gini_npoor*(gini_poor_pc - gini_rich_pc) + gini_rich_pc*gini_pop)/gini_gdp_pc
            gini = gini_num/gini_dnm

            plt.scatter(gini,getcol(res_df,res_head[ipair[1]]), s= 30, 
                        color=brew.get_map('Greys', 'sequential', 9).mpl_colors[7],alpha=0.75,zorder=10)
        
        else:
            plt.scatter(getcol(res_df,res_head[ipair[0]]),getcol(res_df,res_head[ipair[1]]), s= 30, 
                        color=brew.get_map('Greys', 'sequential', 9).mpl_colors[7],alpha=0.75,zorder=10)
        
            plot_trendline(getcol(res_df,res_head[ipair[0]]),getcol(res_df,res_head[ipair[1]]))
    
        plt.xlabel(ipair[0],fontsize=12)
        if ipair[0] in plot_dim: plt.xlim(plot_dim[ipair[0]][0],plot_dim[ipair[0]][1])
    
        plt.ylabel(ipair[1],fontsize=12)
        if ipair[1] in plot_dim: plt.ylim(plot_dim[ipair[1]][0],plot_dim[ipair[1]][1])

        annotate("PSA data", xy=(0.9,0.97),xycoords='axes fraction',fontsize=8,weight='bold',va="top", ha="center")
        plt.savefig(anOption[1]+ipair[0]+'_VS_'+ipair[1]+'.pdf',bbox_inches='tight',format='pdf')

    plt.close('all')

    # Histograms
    plt.style.use('seaborn-deep')

    for ihist in res_head:

        if ihist == 'province' : continue
        if len(set(getcol(res_df,res_head[ihist]))) <= 1: continue

        plt.cla()

        if ihist in ['cp','cr']:

            bins = np.linspace(50, 350, 30)
            plt.hist([getcol(res_df,res_head['cp']),
                      getcol(res_df,res_head['cr']),
                      getcol(res_df,res_head['gdp_pc_pp'])], bins,
                     label=['Consumption (poor)','Consumption (non-poor)','Consumption (avg.)'],histtype='bar',normed=False, alpha=0.33)

            #do_norm_fit(plt,getcol(res_df,res_head['cp']),bns=bins,col=def_pal[0])
            #do_norm_fit(plt,getcol(res_df,res_head['cr']),bns=bins,col=def_pal[1])
            #do_norm_fit(plt,getcol(res_df,res_head['gdp_pc_pp']),bns=bins,col=def_pal[2])

            plt.legend()

        elif ihist in ['social_p','social_r']:
        
            bins = np.linspace(0, 0.35, 20)
            plt.hist([getcol(res_df,res_head['social_p']),
                      getcol(res_df,res_head['social_r'])], bins,
                     label=['Social (poor)','Social (non-poor)'],histtype='bar',normed=False, alpha=0.33)

            do_norm_fit(plt,getcol(res_df,res_head['social_p']),bns=bins,col=def_pal[0])
            do_norm_fit(plt,getcol(res_df,res_head['social_r']),bns=bins,col=def_pal[1])

            plt.legend()        

        elif ihist in ['shewp','shewr']:
            bins = np.linspace(0, 0.3, 20)
            plt.hist([getcol(res_df,res_head['shewp']),
                      getcol(res_df,res_head['shewr'])], bins,
                     label=['Access to early warning (poor)','Access to early warning (non-poor)'],histtype='bar',normed=False, alpha=0.33)
            plt.legend()        

        else:
            n, bins, patches = plt.hist(getcol(res_df,res_head[ihist]), 25, normed=False, alpha=0.5)

        plt.xlabel(ihist,fontsize=12)
        plt.ylabel('n Provinces',fontsize=12)
        annotate("PSA data", xy=(0.1,0.97),xycoords='axes fraction',fontsize=8,weight='bold',va="top", ha="center")
        plt.savefig(anOption[1]+'hist_'+ihist+'.pdf',bbox_inches='tight',format='pdf')
        plt.cla()

    # Scatter plots
    # --> This run
    scatter_data = getcol(res_df,[res_head['risk_to_assets'],res_head['risk'],res_head['resilience'],res_head['pop'],res_head['gdp_pc_pp']])
    df = pd.DataFrame(scatter_data, columns=['risk_to_assets','risk','resilience','pop','gdp_pc_pp'],index=getcol(res_df,res_head['province']))
    df.index.name='province'
    df = df.reset_index()
    df.index.name='position'
    df = df.reset_index().set_index('province')

    df['risk_to_assets']*=100
    df['risk']*=100
    df['resilience']*=100

    # --> Nominal data: this grabs the nominal/baseline run
    if anOption[1] == dbdir:
        ndf = df.copy()

    # Function assigns quartiles to GDP system
    df['gdp'], df['gdpl'] = categorize_GDP(df)

    for iPlt in ['resilience','risk','risk_to_assets']:

        ##########
        # Plot alphabetically
        plt.cla()

        df = df.sort_values('position',axis=0)

        ax = df.plot(kind='scatter',x=[],y=[],s=150,alpha=0.25,color=def_pal[0],label='1st Quartile')
        df.plot(kind='scatter',ax=ax,x=[],y=[],s=300,alpha=0.25,color=def_pal[0],label='2nd Quartile')
        df.plot(kind='scatter',ax=ax,x=[],y=[],s=700,alpha=0.25,color=def_pal[0],label='3rd Quartile')
        df.plot(kind='scatter',ax=ax,x=[],y=[],s=1500,alpha=0.25,color=def_pal[0],label='4th Quartile')

        df.plot(ax=ax, kind='scatter',figsize=[16.0,4.0],
                x='position',y=iPlt,xticks=df.position,rot=90,
                xlim=[-1,79], s=df['gdp'],alpha=0.5)
        leg = ax.legend(title='Provincial GDP',labelspacing=0.75,ncol=1,fontsize=9,borderpad=0.75,fancybox=True,frameon=True,framealpha=0.9)
        leg.get_frame().set_facecolor('white')            

        if 'risk' in iPlt: plt.gca().set_ylim(bottom=-0.01)

        ax.set_xticklabels(df.index.values)

        plt.xlabel('Province',fontsize=12)
        plt.ylabel(iPlt.replace('_',' ').replace('r','R')+' [%]',fontsize=12)
        
        plt.savefig(anOption[1]+'scatter_'+iPlt+'.pdf',bbox_inches='tight',format='pdf')

        ##########
        # Plot in ascending order
        df = df.sort_values(iPlt,axis=0)
        df = df.reset_index()
        df.index.name='position2'
        df = df.reset_index().set_index('province')

        # assign index in ascending order, according to new calculations
        ndf['position2'] = df['position2']

        ax = df.plot(kind='scatter',x=[],y=[],s=150,alpha=0.25,color=def_pal[0],label='1st Quartile')
        df.plot(kind='scatter',ax=ax,x=[],y=[],s=300,alpha=0.25,color=def_pal[0],label='2nd Quartile')
        df.plot(kind='scatter',ax=ax,x=[],y=[],s=700,alpha=0.25,color=def_pal[0],label='3rd Quartile')
        df.plot(kind='scatter',ax=ax,x=[],y=[],s=1500,alpha=0.25,color=def_pal[0],label='4th Quartile')

        df.plot(ax=ax,kind='scatter',figsize=[16.0,4.0],
                x='position2',y=iPlt,xticks=df.position2,rot=90,
                xlim=[-1,79],s=df['gdp'],alpha=0.5)
        leg = ax.legend(title='Provincial GDP',loc='upper left',labelspacing=0.75,ncol=1,fontsize=9,borderpad=0.75,fancybox=True,frameon=True,framealpha=0.9)
        leg.get_frame().set_facecolor('white')

        if 'risk' in iPlt: plt.gca().set_ylim(bottom=-0.01)

        ax.set_xticklabels(df.index.values)

        plt.xlabel('Province',fontsize=12)
        plt.ylabel(iPlt.replace('_',' ').replace('r','R')+' [%]',fontsize=12)

        plt.savefig(anOption[1]+'sort_scatter_'+iPlt+'.pdf',bbox_inches='tight',format='pdf')

        ##########
        # Plot in ascending order without GDP/size
        ax = df.plot(kind='scatter',figsize=[16.0,4.0],
                     x='position2',y=iPlt,xticks=df.position2,rot=90,
                     xlim=[-1,79],alpha=0.5)
    
        # This line plots the baseline results over the policy options
        if anOption[1] != dbdir:
            
            df.plot(ax=ax,kind='scatter',x=[],y=[],alpha=0.5,color='grey',label='A')
            df.plot(ax=ax,kind='scatter',x=[],y=[],alpha=0.5,label='B')
            
            ndf.plot(ax=ax,kind='scatter',figsize=[16.0,4.0],
                     x='position2',y=iPlt,xticks=df.position2,rot=90,
                     xlim=[-1,79],color='grey',alpha=0.5)
            
            leg = ax.legend(title='Policy',loc='upper left',labelspacing=0.75,ncol=1,fontsize=9,borderpad=0.75,fancybox=True,frameon=True,framealpha=0.9)
            leg.get_frame().set_facecolor('white')

        if 'risk' in iPlt: plt.gca().set_ylim(bottom=-0.5)

        ax.set_xticklabels(df.index.values)

        plt.xlabel('Province',fontsize=12)
        plt.ylabel(iPlt.replace('_',' ').replace('r','R')+' [%]',fontsize=12)

        plt.savefig(anOption[1]+'sort_scatter_noGDP_'+iPlt+'.pdf',bbox_inches='tight',format='pdf')
    
        df = df.drop('position2',axis=1)

    #########
    # Box plots
    plt.cla()
    plt.figure(figsize=[6.0,4.4])
    #
    comp_str = 'risk_to_assets'
    #
    cons_data = getcol(res_df,[res_head['cp'],res_head['gdp_pc_pp'],res_head['cr'],res_head[comp_str]])
    df = pd.DataFrame(cons_data, columns=['cp','ct','cr',comp_str],index=getcol(res_df,res_head['province']))
    df.index.name = 'province'

    df = df.reset_index().set_index([comp_str])
    df = df.sort_index()

    df = df.reset_index().set_index(['province'])
    value_dict = df[comp_str].to_dict()

    df = df.drop([comp_str],axis=1)

    head_and_tail = [df.head(10),df.tail(10)]
    result = pd.concat(head_and_tail)

    positions = [i for i in range(10)]+[i for i in range(11,21)]
    positions_all = [i for i in range(len(result))]

    color = dict(boxes='DarkGreen', whiskers='DarkOrange', medians='DarkBlue', caps='Gray')

    ax = result.T.plot(kind='box',rot=80,color=color,positions=positions,return_type='axes')

    plt.subplots_adjust(bottom=0.30)

    plt.ylabel("Income per cap. (poor - avg - nonpoor)",fontsize=10)
    plt.tick_params(axis='both', which='major', labelsize=8)

    for iloc, itick in enumerate(plt.gca().get_xticklabels()):
        
        jtick = str(itick.get_text())
    
        if jtick in value_dict:
            plt.annotate(str(int(value_dict[jtick]*100)),xy=(positions[iloc],54),xycoords='data',fontsize=7,va="center", ha="center")

    plt.annotate("10 lowest-"+comp_str+" provinces", xy=(0.25,-0.35),xycoords='axes fraction',fontsize=8,weight='bold',va="top", ha="center",clip_on=False)
    plt.annotate("10 highest-"+comp_str+" provinces", xy=(0.75,-0.35),xycoords='axes fraction',fontsize=8,weight='bold',va="top", ha="center",clip_on=False)

    plt.draw()

    plt.savefig(anOption[1]+'boxplot_'+comp_str+'.pdf',bbox_inches='tight',format='pdf')
    
    plt.close('all')
