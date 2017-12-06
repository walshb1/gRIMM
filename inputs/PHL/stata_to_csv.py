import pandas as pd

data = pd.io.stata.read_stata('FIES2015_v2v4fin.dta')
data.to_csv('FIES2015_v2v4fin.csv')
