import gc
import gdal
import glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sys
%matplotlib inline

myC = 'CO'

# Function to load GEOTIFFS filetypes,
def gtiff_to_array(fname, get_global = False):
    """Open a gtiff and convert it to an array.  Store coordinates in global variables if toggle is on"""
    tif = gdal.Open(fname)
    a = tif.ReadAsArray()
    gt = tif.GetGeoTransform()
    print(gt)
    if get_global:
        print(gdal.Info(tif))
        global lons, lats, loni, lati, xx, yy, xi, yi
        lons = np.array([round(gt[0]+gt[1]*i,5) for i in range(a.shape[1])])
        lats = np.array([round(gt[3]+gt[5]*i,5) for i in range(a.shape[0])])
        loni = np.array([i for i in range(a.shape[1])])
        lati = np.array([i for i in range(a.shape[0])])
        xx,yy = np.meshgrid(lons, lats)
        xi,yi = np.meshgrid(loni,lati)
    return

if False:
    # Make an area weighted fa
    rps = [5,10,20,50,75,100,200,250,500,1000]
    d = {}
    for rp in rps:
        flist = sorted(glob.glob('./CO_pluvial_defended/CO-PD-{}-*.tif'.format(rp)))
        dic = {}
        for f in flist:
            a = gtiff_to_array(f)
            a[a == -9999] = np.nan
            a[a == 999] = np.nan
            vals = a.ravel()[~np.isnan(a.ravel())]
            s = pd.Series(vals)
            dic[f] = len(s), pd.cut(s,list(np.arange(0,5,0.5)) + [10, np.inf], right = True).value_counts().sort_index()
        s = pd.Series(index=dic[f][1].index, data = 0)
        pop = 0
        for f in dic.keys():
            s+=dic[f][1]
            pop += dic[f][0]
        d[rp] = s/pop*100
        break
    pd.DataFrame(d).to_csv('spatial_fas.csv')

if True:
    dic = {}
    rps = [5,10,20,50,75,100,200,250,500,1000]
    for rp in rps:
        flist = sorted(glob.glob('./CO_pluvial_defended/CO-PD-{}-*.tif'.format(rp)))
        # print(maplist, flist)
        lis = []
        space_tile = []
        for i in range(len(flist)):
            f = flist[i]
            # The tile numbers should always match up here
            print(map, f)
            flood = gtiff_to_array(f)

            total_cells = np.logical_and(flood>-9999, flood<999).sum()
            flood_cells = np.logical_and(flood>0, flood<999).sum()

            lis.append(flood_cells)
            space_tile.append(total_cells)
        dic[rp] = lis
    dic['pop']= space_tile
    df = pd.DataFrame(dic).rename({'pop':'space'},axis=1)

    df.loc['total'] = df.sum(axis=0)
    df.to_csv('space_affected.csv', index = False)
    for rp in rps:
        df[rp] = df[rp].divide(df['space'])
    df.to_csv('space_fa.csv',index = False)


if True:
    #Make resampled population maps that match the SSBN maps
    rp = 5
    flist = sorted(glob.glob('./CO_pluvial_defended/CO-PD-{}-*.tif'.format(rp)))
    for f in flist:
        print('Processing...', f)
        tif = gdal.Open(f)
        tileno = f[-5]
        gt = tif.GetGeoTransform()
        bounds = [gt[0],gt[3],gt[0]+gt[1]*tif.RasterXSize, gt[3]+gt[5]*tif.RasterYSize]
        # https://gdal.org/python/osgeo.gdal-module.html#TranslateOptions
        pop = gdal.Open("gpw_v4_population_count_rev11_2015_30_sec.tif")
        # Sample for what this would look like in the commmand line
        # Big Argentina map
        # gdal_translate -ot Float32 -r near -tr 0.000833333333333 0.000833333333333 -projwin -73.6333333333333 -21.733333333333 -52.8 -55.9 -co COMPRESS=DEFLATE gpw_v4_population_count_rev11_2015_30_sec.tif CO_v4_population_count_2015_3_sec.tif
        # Overlay tile 1
        # gdal_translate -ot Float32 -r near -tr 0.000833333333333 0.000833333333333 -projwin -73.6333333333333 -21.733333333333 -63.2166666 -30.275 -co COMPRESS=DEFLATE gpw_v4_population_count_rev11_2015_30_sec.tif CO_v4_population_count_2015_3_sec-1.tif
        # Tile 2
        # gdal_translate -ot Float32 -r near -tr 0.000833333333333 0.000833333333333 -projwin -73.6333333333333 -21.733333333333 -63.2166666 -30.275 -co COMPRESS=DEFLATE gpw_v4_population_count_rev11_2015_30_sec.tif CO_v4_population_count_2015_3_sec-1.tif
        gdal.Translate('CO_v4_population_count_rev11_2015_3_sec-{}.tif'.format(tileno), pop, xRes = gt[1], yRes = gt[1], projWin = bounds, resampleAlg = 'near', creationOptions = ["COMPRESS=DEFLATE"])

if True:
    dic = {}
    div = 10
    rps = [5,10,20,50,75,100,200,250,500,1000]
    for rp in rps:
        # These always should match up
        maplist = sorted(glob.glob('CO_v4_population_count_rev11_2015_3_sec-*.tif'))
        flist = sorted(glob.glob('./CO_pluvial_defended/CO-PD-{}-*.tif'.format(rp)))
        # print(maplist, flist)
        lis = []
        pop_tile = []
        for i in range(len(maplist)):
            map = maplist[i]
            f = flist[i]
            # The tile numbers should always match up here
            print(map, f)
            pops = gtiff_to_array(map)/100 # Divide by hundred because we just resampled the nearest neighbor, grid dims for the flist are 10x
            pops[pops<-1e36] = 0
            flood = gtiff_to_array(f)
            # SOME WORK TO
            # assert flood.shape == pops.shape
            # shape = np.array(flood.shape)
            # gridsize = shape//div
            # dimensions = shape//div*0.00083 # Dimensions in coordinate degrees
            # xis = range(div)*gridsize[0]
            # yis = range(div)*gridsize[1]
            # from itertools import product
            # list(product(xis,yis))
            #
            flood[flood==-9999] = 0
            flood[flood==999] = 0

            lis.append(np.sum(pops*flood.astype(bool)))
            pop_tile.append(np.sum(pops))
        dic[rp] = lis
    df = pd.DataFrame(dic)
    df['pop'] = pop_tile
    df.loc['total'] = df.sum(axis=0)
    df.to_csv('pop_affected.csv', index = False)
    for rp in rps:
        df[rp] = df[rp].divide(df['pop'])*100
    df.to_csv('pop_fa.csv',index = False)

def random_to_loss(County,pval):
    for _nrp, _rp in enumerate(inv_rps):
        if pval > _rp:
            try: return int(_df.loc[(County,rps[_nrp-1])])
            except: return 0
            # ^ this is because the RP=0 isn't in the df
    # print(_df.loc[(County,rps[-1])].values)
    return int(_df.loc[(County,rps[-1])])


def gricells_to_adm0(myC = 'CO', _haz='PF', src = 'pop_affected.csv'):
    """Assumes perfect correlation within an individual grid cell and resample the exceedance curve from the grid cell level to the national level
    This is to lower the overestimation of impacts since a 1000 year flood doesn't affect the whole country at the maximum exceedance at the same time"""
    global _df
    var = src[:src.index('_')]
    _df = pd.read_csv(src).drop(var, axis = 1)
    _df.index.name = 'gridcell'
    _df.columns.name = 'rp'
    _df.columns = _df.columns.astype(int)
    _df = _df.stack().to_frame()
    global rps,inv_rps
    rps = list(_df.index.levels[1].astype(int))
    if rps[0] != 1.: rps = np.append([1.],[rps])
    inv_rps = [1/i for i in rps]
    #print(rps)
    final_rps = [1, 20, 50, 100,250, 500, 1000,1500,2000]
    final_exceedance = pd.DataFrame(index= pd.MultiIndex.from_product([[myC],final_rps]))
    final_exceedance['loss'] = None

    # create dataframe to store random numbers
    loss = pd.DataFrame(index=_df.sum(level='gridcell').index).reset_index()
    loss['myC'] = myC
    loss.set_index(['myC','gridcell'], inplace = True)
    lossc = loss.sum(level = 'myC')
    loss = loss.reset_index().set_index('myC')

    # generate random numbers
    NYECOS = int(1E4) # <-- any multiple of 10K
    for _yn in range(NYECOS):
        loss['_'] = [np.random.uniform(0,1) for i in range(loss.shape[0])]
        loss['y'+str(_yn)] = loss.apply(lambda x:random_to_loss(x.gridcell,x['_']),axis=1)

        if _yn != 0 and (_yn+1)%500 == 0:

            lossc = pd.concat([lossc,loss.drop('_',axis=1).sum(level='myC')],axis=1)
            loss = loss[['gridcell']]
            print(_yn+1)

    for _reg in loss.index.values:
        aReg = lossc.loc[_reg].sort_values(ascending=False).reset_index()

        for _frp in final_rps:
            final_exceedance.loc[(_reg,_frp),'loss'] = float(aReg.iloc[int((NYECOS-1)/_frp)][_reg])

    total_pop = pd.read_csv('{}_affected.csv'.format(var))[var].sum()
    (final_exceedance/total_pop).to_csv('../inputs/'+myC+'regional_exceedance_'+_haz+src[:2]+'.csv')

gricells_to_adm0(src = 'pop_affected.csv')
gricells_to_adm0(src = 'space_affected.csv')
