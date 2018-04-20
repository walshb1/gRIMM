####################################################################
# This script scrapes country credit ratings from https://tradingeconomics.com/country-list/rating
# -- run with "scrapy runspider lib_get_ratings.py" from the command prompt
# -- Written on 19 April 2018 by bwalsh

import scrapy
import pandas as pd

class RatingsSpider(scrapy.Spider):
    name = "trading_econ"
    start_urls = ['https://tradingeconomics.com/country-list/rating']

    #def parse(self, response):
    #    SET_SELECTOR = '.bold'
    #    for brickset in response.css(SET_SELECTOR):
    #        
    #        NAME_SELECTOR = '::text'
    #
    #        yield {
    #            'name': brickset.css(NAME_SELECTOR).extract_first().replace(' ','').replace('\r\n',''),
    #        }

    def parse(self, response):
        SET_SELECTOR = 'table'
        cdict = []
        rdict = []

        for brickset in response.css(SET_SELECTOR):
            
            #NAME_SELECTOR = 'a::text'
            #yield {
            #    'name': brickset.css(NAME_SELECTOR).extract(),
            #    'span': brickset.css('span::text').extract(),   
            #}
            
            for c in brickset.css('a::text').extract():
                #yield {c.replace(' ','').replace('\r\n','')}
                cdict.append(c.replace(' ','').replace('\r\n',''))
            
            for r in brickset.css('span::text').extract():
                rdict.append(r.replace(' ','').replace('\r\n','').replace('\t',''))

        crdict = pd.DataFrame(columns=['S&P',"Moody's",'Fitch','DBRS','TE'],index=cdict)
        crdict.index.name = 'country_in_ratings'

        offset = 0
        for n,c in enumerate(cdict):
            n = n*5+offset
            noTE = False

            # These are the countries that don't have a value for TE
            # - Unlike the other columns, the crawler doesn't leave a space for them, which shifts everything subsequent
            # - trying not to spend time, so I just treat them separately here. edit the list if any are assigned TE values
            if c in ['Grenada','Maldives','Swaziland','Tajikistan','Tanzania']: 
                offset-=1
                noTE = True

            if not noTE:
                try: crdict.loc[c] = [rdict[n],rdict[n+1],rdict[n+2],rdict[n+3],rdict[n+4]]
                except: pass
            else: 
                try: crdict.loc[c] = [rdict[n],rdict[n+1],rdict[n+2],rdict[n+3],'N/A']
                except: pass

        crdict.to_csv('inputs/credit_ratings_scrapy.csv')

        print(cdict)
        print(rdict)
        
