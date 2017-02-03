from pylab import *
import csv
import prettyplotlib as ppl
import matplotlib.patches as pts
from matplotlib import rc
from matplotlib import colors
from textwrap import wrap
import os
rc('text', usetex=False)

#Aesthetics
import seaborn as sns
import brewer2mpl as brew
from matplotlib import colors

def isFloat(string,ndec=10):
    try:
        float(string)
        return round(float(string),ndec)
    except ValueError:
        return string

def getcol(array, index):
    return [xrow[index] for xrow in array]

head = {}
df = []

# read in output file
cdir   = os.getcwd()          # current directory
dbdir  = cdir+'/debug_plots/' # plots go here
if not os.path.exists(dbdir): 
    os.makedirs(dbdir)

with open('output/PHL_results_tax_no.csv') as f:
    reader = csv.reader(f)

    for idx, irow in enumerate(reader):

        irow = str(irow).replace('[','').replace(']','').replace("'",'').replace(' ','').split(',')

        for jdx, jcol in enumerate(irow):
            irow[jdx] = isFloat(jcol)
    
        if idx == 0:
            for jdx, jcol in enumerate(irow):
                head[jcol] = jdx

            print('\n---> Debug plot options: (pick 2)\n',[keys for keys in head],'\n')
            
        else: df.append(irow)  

plot_pairs = [['gdp_pc_pp','risk'],
              ['gdp_pc_pp','resilience'],
              ['gdp_pc_pp','risk_to_assets'],
              ['gdp_pc_pp','pov_head'],
              ['gdp_pc_pp','cp'],
              ['gdp_pc_pp','cr'],
              ['gdp_pc_pp','protection'],
              ['gdp_pc_pp','dWpc_currency'],
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
              ['cp','cr']]

plot_dim = {'delta_W':[0,0.0002],
            'risk':[0.1,0.2],
            'fa':[0.08,0.12]}

for ipair in plot_pairs:
    plt.cla()
    plt.scatter(getcol(df,head[ipair[0]]),getcol(df,head[ipair[1]]), s= 30, color=brew.get_map('Greys', 'sequential', 9).mpl_colors[7],alpha=0.75,zorder=10)
    
    plt.xlabel(ipair[0],fontsize=12)
    if ipair[0] in plot_dim: plt.xlim(plot_dim[ipair[0]][0],plot_dim[ipair[0]][1])
    
    plt.ylabel(ipair[1],fontsize=12)
    if ipair[1] in plot_dim: plt.ylim(plot_dim[ipair[1]][0],plot_dim[ipair[1]][1])

    annotate("PHL provincial data", xy=(0.9,0.97),xycoords='axes fraction',fontsize=8,weight='bold',va="top", ha="center")
    plt.savefig(dbdir+ipair[0]+'_VS_'+ipair[1]+'.pdf',bbox_inches='tight',format='pdf')
